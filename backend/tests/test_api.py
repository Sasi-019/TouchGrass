"""End-to-end smoke test of the whole loop, with the AI and the internet faked:

Sign up -> sign in -> profile -> agent (tools + validation) -> history
-> feedback -> memory/profile learning -> next recommendation avoids repeats.
"""

import uuid

EMAIL = f"tester-{uuid.uuid4().hex[:8]}@example.com"
PASSWORD = "correct horse battery"

ACTIVITY = {
    "intent": "activity",
    "reply": "Here's a challenge.",
    "reason": "You love photography.",
    "activity": {
        "title": "Nature Texture Hunt",
        "description": "Spend 30 minutes finding unusual natural textures. "
                       "Take only one final photograph.",
        "category": "outdoors", "duration_minutes": 30,
        "location_type": "outdoors", "screen_use": "low", "difficulty": "easy",
        "related_interests": ["photography"],
        "place": {"name": "Lakeside Park", "type": "park"},
        "reason": "You love photography.",
    },
}


def _auth(client):
    client.post("/auth/signup", json={"name": "Tess", "email": EMAIL, "password": PASSWORD})
    token = client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_and_cors(client):
    assert client.get("/health").json()["database"] == "connected"

    preflight = client.options(
        "/agent/chat",
        headers={"Origin": "http://localhost:5173",
                 "Access-Control-Request-Method": "POST"},
    )
    assert preflight.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_auth_rules(client):
    ok = client.post("/auth/signup", json={"name": "A", "email": EMAIL, "password": PASSWORD})
    assert ok.status_code in (201, 400)  # 400 if an earlier test created it

    assert client.post("/auth/signup", json={"name": "A", "email": EMAIL, "password": PASSWORD}).status_code == 400
    assert client.post("/auth/register", json={"name": "A", "email": EMAIL, "password": PASSWORD}).status_code == 400  # alias exists
    assert client.post("/auth/login", json={"email": EMAIL, "password": "wrong-password"}).status_code == 401
    assert client.post("/auth/signup", json={"name": "A", "email": "b@example.com", "password": "short"}).status_code == 422

    assert client.get("/profile").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer nonsense"}).status_code == 401


def test_full_personalisation_loop(client, scripted_ai):
    headers = _auth(client)

    # Profile discovery -> AI-understood profile -> saved.
    assert client.get("/profile", headers=headers).status_code == 404

    saved = client.post("/profile", headers=headers, json={
        "interests": [{"name": "photography", "strength": 0.8},
                      {"name": "nature", "strength": 0.7}],
        "wants_more_of": ["time outdoors"], "curiosity": ["gardening"],
        "experience_preferences": ["explore"], "dislikes": ["crowded places"],
        "constraints": [], "typical_free_time": "20-40 minutes",
        "adventure_level": "moderate",
    })
    assert saved.status_code == 200

    # Conversational agent with browser location -> tools -> one challenge.
    scripted_ai.plan = {**scripted_ai.plan, "intent": "activity",
                        "tools": ["weather", "nearby_places"]}
    scripted_ai.replies = [ACTIVITY]

    chat = client.post("/agent/chat", headers=headers, json={
        "message": "I have 30 minutes and want to go outside",
        "latitude": 12.97, "longitude": 77.59, "timezone": "Asia/Kolkata",
    })
    assert chat.status_code == 200, chat.text
    body = chat.json()
    assert body["activity"]["title"] == "Nature Texture Hunt"
    assert body["activity"]["place"]["name"] == "Lakeside Park"
    assert body["weather"]["summary"].startswith("clear")
    assert body["nearby_places"][0]["name"] == "Lakeside Park"
    activity_id = body["activity_id"]

    # Saved in the database with its context.
    history = client.get("/activities", headers=headers).json()
    assert history[0]["id"] == activity_id
    assert history[0]["context"]["weather"].startswith("clear")
    assert history[0]["context"]["approximate_location"] == {"latitude": 12.97, "longitude": 77.59}

    # Feedback updates the memory.
    scripted_ai.memory = {
        "boost_interests": ["photography"],
        "add_interests": [{"name": "plants", "strength": 0.5}],
        "note": "Enjoys searching for unusual plants.",
    }
    feedback = client.post(f"/activities/{activity_id}/feedback", headers=headers, json={
        "rating": 5, "completed": "yes",
        "comment": "I loved searching for unusual plants",
    })
    assert feedback.status_code == 200
    assert feedback.json()["memory_note"] == "Enjoys searching for unusual plants."

    profile = client.get("/profile", headers=headers).json()
    names = {i["name"]: i["strength"] for i in profile["interests"]}
    assert names["photography"] > 0.8          # strengthened
    assert "plants" in names                   # discovered
    assert profile["learned_notes"][-1]["rating"] == 5

    assert client.get(f"/activities/{activity_id}", headers=headers).json()["status"] == "completed"

    # Next request: the model repeats itself first; validation forces a new one.
    different = {**ACTIVITY, "activity": {
        **ACTIVITY["activity"], "title": "Sound Map Walk",
        "description": "Sit still for ten minutes and draw every sound you hear.",
        "place": None}}
    scripted_ai.plan = {**scripted_ai.plan, "tools": []}
    scripted_ai.replies = [ACTIVITY, different]

    again = client.post("/agent/chat", headers=headers, json={"message": "give me something to do"})
    assert again.status_code == 200
    assert again.json()["activity"]["title"] == "Sound Map Walk"
    assert scripted_ai.replies == []           # both proposals were consumed


def test_users_cannot_touch_each_others_data(client, scripted_ai):
    headers = _auth(client)

    scripted_ai.replies = [ACTIVITY]
    activity_id = client.post("/agent/chat", headers=headers,
                              json={"message": "something to do"}).json()["activity_id"]

    other_email = f"other-{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/signup", json={"name": "O", "email": other_email, "password": PASSWORD})
    token = client.post("/auth/login", json={"email": other_email, "password": PASSWORD}).json()["access_token"]
    other = {"Authorization": f"Bearer {token}"}

    assert client.get(f"/activities/{activity_id}", headers=other).status_code == 404
    assert client.post(f"/activities/{activity_id}/feedback", headers=other,
                       json={"rating": 5}).status_code == 404


def test_works_without_location_and_when_ai_is_down(client, scripted_ai, monkeypatch):
    headers = _auth(client)

    # No coordinates at all: still answers.
    scripted_ai.replies = [{"intent": "chat", "reply": "Hi! What are you in the mood for?",
                            "reason": None, "activity": None}]
    scripted_ai.plan = {**scripted_ai.plan, "intent": "chat"}
    ok = client.post("/agent/chat", headers=headers, json={"message": "hello"})
    assert ok.status_code == 200 and ok.json()["activity"] is None

    # AI failure -> friendly 502, not a stack trace.
    import app.agent_graph as agent_graph
    from app.ai_service import AIServiceError

    def boom(*args, **kwargs):
        raise AIServiceError("down")

    monkeypatch.setattr(agent_graph, "generate_json", boom)
    failed = client.post("/agent/chat", headers=headers, json={"message": "surprise me"})
    assert failed.status_code == 502
    assert "unavailable" in failed.json()["detail"].lower()


def test_voice_endpoint(client, monkeypatch):
    headers = _auth(client)

    import app.routers.voice as voice

    monkeypatch.setattr(voice, "transcribe_audio", lambda audio_bytes, filename: "I have thirty minutes")

    good = client.post("/voice/transcribe", headers=headers,
                       files={"file": ("voice.webm", b"fake-audio", "audio/webm")})
    assert good.status_code == 200 and good.json()["text"] == "I have thirty minutes"

    legacy_field = client.post("/voice/transcribe", headers=headers,
                               files={"audio": ("recording.webm", b"fake-audio", "audio/webm")})
    assert legacy_field.status_code == 200

    assert client.post("/voice/transcribe", headers=headers).status_code == 400
    assert client.post("/voice/transcribe",
                       files={"file": ("voice.webm", b"x", "audio/webm")}).status_code == 401


def test_chat_history_is_saved_and_private(client, scripted_ai):
    # A brand-new user, so earlier tests' activities can't trigger the
    # repetition check and change the scripted flow.
    email = f"history-{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/signup", json={"name": "Hana", "email": email, "password": PASSWORD})
    token = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Start from a clean conversation.
    assert client.delete("/agent/history", headers=headers).status_code == 200
    assert client.get("/agent/history", headers=headers).json() == []

    scripted_ai.plan = {**scripted_ai.plan, "intent": "activity", "tools": []}
    scripted_ai.replies = [ACTIVITY]

    chat = client.post("/agent/chat", headers=headers, json={
        "message": "Give me something to do",
    })
    assert chat.status_code == 200, chat.text
    body = chat.json()
    assert isinstance(body["needs_location"], bool)

    # Both sides of the conversation come back, oldest first, and the
    # assistant message carries its challenge so the card can be re-shown.
    history = client.get("/agent/history", headers=headers).json()
    assert [m["role"] for m in history] == ["user", "assistant"]
    assert history[0]["content"] == "Give me something to do"
    assert history[1]["activity"]["id"] == body["activity_id"]
    assert history[1]["activity"]["title"] == "Nature Texture Hunt"

    # History needs a login.
    assert client.get("/agent/history").status_code == 401

    # Another user never sees it.
    other = client.post("/auth/signup", json={
        "name": "Other", "email": f"other-{uuid.uuid4().hex[:8]}@example.com",
        "password": PASSWORD,
    })
    assert other.status_code == 201
    other_token = client.post("/auth/login", json={
        "email": other.json()["email"], "password": PASSWORD,
    }).json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}
    assert client.get("/agent/history", headers=other_headers).json() == []

    # "New chat" clears messages but keeps the activity.
    assert client.delete("/agent/history", headers=headers).json()["deleted"] == 2
    assert client.get("/agent/history", headers=headers).json() == []
    assert any(
        a["id"] == body["activity_id"]
        for a in client.get("/activities", headers=headers).json()
    )

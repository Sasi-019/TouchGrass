"""Shared test setup.

The environment is configured BEFORE the app is imported, because the app
validates its configuration at import time. Tests use a throw-away SQLite file
and fake keys; nothing here talks to Groq, PostgreSQL or the internet.
"""

import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="touchgrass-tests-")

os.environ["APP_ENV"] = "development"
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["JWT_SECRET"] = "test-secret-" + "x" * 40
os.environ["GROQ_API_KEY"] = "test-key-not-real"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session")
def client():
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def scripted_ai(monkeypatch):
    """Replace every Groq call with scripted answers.

    Planner calls get ``plan``; agent/memory calls pop from ``replies``.
    """

    class Script:
        plan: dict = {
            "intent": "activity", "tools": [], "location": None,
            "category": "all", "needs_location": False,
            "available_minutes": None, "energy": None,
            "social": None, "setting": None,
        }
        replies: list = []
        memory: dict = {}
        calls: list = []

    script = Script()
    script.replies = []
    script.calls = []

    def fake_generate_json(system_prompt, user_prompt, temperature=0.2, max_tokens=800):
        script.calls.append(system_prompt[:40])

        if "planning step" in system_prompt:
            return dict(script.plan)

        if "memory-update step" in system_prompt:
            return dict(script.memory)

        return script.replies.pop(0)

    import app.agent_graph as agent_graph
    import app.ai_service as ai_service

    monkeypatch.setattr(agent_graph, "generate_json", fake_generate_json)
    monkeypatch.setattr(ai_service, "generate_json", fake_generate_json)

    # No real network for the tools either.
    import app.real_world_tools as world

    monkeypatch.setattr(
        world, "get_weather",
        lambda **kwargs: {
            "ok": True, "location": "Testville",
            "summary": "clear sky, 22°C", "outdoor_ok": True, "is_wet": False,
        },
    )
    monkeypatch.setattr(
        world, "search_nearby_places",
        lambda **kwargs: {
            "ok": True, "search_area": "Testville",
            "places": [
                {"name": "Lakeside Park", "type": "park", "distance_m": 400},
            ],
        },
    )

    return script

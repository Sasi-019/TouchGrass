# TouchGrass

**A personalized AI agent that gets you off the screen.** TouchGrass learns what
you enjoy, checks what is realistic right now (time, weather, optional
location), and gives you **one** offline challenge. You do it, come back for a
rating, and the next challenge gets better.

> "The screen should be the shortest part of the experience."

```
Sign Up → Profile Discovery → AI-understood Profile → Home → Ask the agent
→ LangGraph + tools → one offline challenge → do it → feedback
→ memory/profile learning → better future challenges
```

## Stack

| Layer      | Technology                                                  |
|------------|-------------------------------------------------------------|
| Frontend   | React + Vite + Tailwind CSS                                 |
| Backend    | Python, FastAPI, SQLAlchemy                                 |
| Database   | PostgreSQL (structured long-term memory)                    |
| Agent      | LangGraph (stateful workflow with a validation loop)        |
| LLM        | Groq (reasoning) · Groq Whisper (voice transcription)       |
| Tools      | Open-Meteo (weather), OpenStreetMap/Overpass (nearby places), browser geolocation (optional) |
| Auth       | JWT + bcrypt                                                |

## How the agent works

`backend/app/agent_graph.py` runs these steps each time you ask for something:

1. **load_profile** – interests, curiosity, dislikes, constraints, learned notes
2. **load_conversation / load_activity_history** – so it never repeats itself
3. **build_context** – local time, day, available minutes, energy, social mode
4. **plan** – decides the intent (activity, regenerate, adapt, places, question, chat) and which tools are worth calling
5. **execute_tools** – weather, nearby places, user location, current context
6. **generate** – one personalized challenge as JSON
7. **validate** – checks time, weather, dislikes, repetition and screen use; on failure it loops back to *generate* (up to 3 attempts)
8. **finalize → persist** – saves the activity and its context in PostgreSQL

The chat remembers your conversation (`GET /agent/history`, `DELETE /agent/history` for a new chat), so the screen behaves like a normal AI chat and survives reloads.

Feedback (`POST /activities/{id}/feedback`) updates the profile's learned notes,
so later challenges reflect what you loved or avoided. Prompts live in
`backend/app/prompts.py`, separate from user data.

## Run locally

You need Python 3.11+, Node 20+, and PostgreSQL.

### 1. Database

```bash
createdb touchgrass
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then edit .env (see below)
uvicorn app.main:app --reload
```

Fill in `backend/.env`:

- `DATABASE_URL` – e.g. `postgresql://postgres:YOUR_PASSWORD@localhost:5432/touchgrass`
- `JWT_SECRET` – generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- `GROQ_API_KEY` – from https://console.groq.com/keys

If anything required is missing, the server stops at startup and lists every
problem at once. Tables are created automatically on first run, and new columns
are added automatically when you upgrade.

API docs: http://127.0.0.1:8000/docs · health check: http://127.0.0.1:8000/health

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env               # VITE_API_URL defaults to http://127.0.0.1:8000
npm run dev
```

Open http://localhost:5173.

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

The tests use an in-memory SQLite database and stub the network, so they need
no Groq key, internet connection or PostgreSQL.

## Deployment

Recommended: **Vercel** (frontend) + **Render** (backend and PostgreSQL).
Railway or any host that runs Python and Postgres works too.

### Backend on Render

1. Push this repo to GitHub.
2. In Render choose **New → Blueprint** and select the repo. `render.yaml`
   creates the API and a PostgreSQL database and wires `DATABASE_URL` for you.
3. When prompted, set:
   - `GROQ_API_KEY` – your Groq key
   - `CORS_ORIGINS` – your Vercel URL, e.g. `https://touchgrass.vercel.app` (no trailing slash)
4. `JWT_SECRET` is generated for you. Check `https://<your-api>.onrender.com/health`.

(Manual setup: root directory `backend`, build `pip install -r requirements.txt`,
start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, and `APP_ENV=production`.)

### Frontend on Vercel

1. **Add New → Project**, import the repo, set **Root Directory** to `frontend`.
2. Add the environment variable `VITE_API_URL` = your Render API URL.
3. Deploy. `frontend/vercel.json` makes page refreshes like `/home` work.
4. Optional: to allow Vercel preview URLs, set `CORS_ORIGIN_REGEX` on the backend
   (see `backend/.env.example`).

### Production checklist

- [ ] `APP_ENV=production` and a `JWT_SECRET` of 32+ characters
- [ ] `CORS_ORIGINS` lists only your real frontend URL
- [ ] HTTPS everywhere (Vercel and Render provide it)
- [ ] Database encryption at rest (managed Postgres providers include it)
- [ ] No `.env` file committed. Real secrets only in the host's environment settings
- [ ] Browser location and the microphone only work on HTTPS (or localhost)

## Privacy

- Passwords are hashed with bcrypt; plaintext is never stored.
- Every request is authorized by JWT, and users can only read their own data.
- **Location is optional.** Nothing is requested until you press *Use my
  location*, and the coordinates stay in memory only. If you deny it, the app
  keeps working without weather and nearby-place lookups.
- Voice output is off by default, with a Voice ON/OFF switch and a Stop button.
  If voice input fails, you can always type instead.
- Please do not enter sensitive information that is not needed for activities.

## Project layout

```
backend/
  app/
    main.py            FastAPI app, CORS, error handling, /health
    config.py          validated environment settings
    agent_graph.py     LangGraph workflow + tools
    prompts.py         system prompts
    memory_service.py  feedback → profile learning
    ai_service.py      Groq: profile understanding + Whisper
    real_world_tools.py  Open-Meteo / OpenStreetMap helpers
    routers/           auth, profile, activities, agent, voice
  tests/               pytest smoke tests
  legacy/              earlier implementation kept for reference
frontend/src/
  pages/               Landing, SignUp, SignIn, ProfileDiscovery, Home, Profile, Activity
  components/          ActivityCard, VoiceButton, ProfilePanel, RequireAuth
  hooks/               useBrowserLocation, useVoiceOutput
  services/api.js      all backend calls
```

## Roadmap

Google Calendar integration, richer place data, and (once enough feedback has
been collected) fine-tuning an open-weight model.



from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db, check_database_connection

from .routers.auth import router as auth_router
from .routers.profile import router as profile_router
from .routers.activities import router as activities_router
from .routers.agent import router as agent_router
from .routers.voice import router as voice_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n========================================")
    print("Starting TouchGrass backend...")
    print("========================================")

    try:
        init_db()

        if check_database_connection():
            print("PostgreSQL: connected")
        else:
            print("PostgreSQL: connection failed")

    except Exception as exc:
        print("Database initialization error:")
        print(type(exc).__name__, str(exc))

    yield

    print("TouchGrass backend shutting down...")


app = FastAPI(
    title="TouchGrass API",
    description="Personalized real-world activity agent",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(activities_router)
app.include_router(agent_router)
app.include_router(voice_router)

# ============================================================
# BASIC ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {
        "message": "TouchGrass API is running",
        "status": "ok",
    }


@app.get("/health")
def health():
    database_status = check_database_connection()

    return {
        "status": "healthy",
        "database": (
            "connected"
            if database_status
            else "disconnected"
        ),
    }


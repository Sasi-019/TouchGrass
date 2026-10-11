import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Importing database first validates the environment (DATABASE_URL,
# JWT_SECRET, GROQ_API_KEY ...) and stops with one clear message if
# anything is missing.
from .database import init_db, check_database_connection
from .config import get_settings

from .routers.auth import router as auth_router
from .routers.profile import router as profile_router
from .routers.activities import router as activities_router
from .routers.agent import router as agent_router
from .routers.voice import router as voice_router

logger = logging.getLogger("touchgrass")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting TouchGrass backend (%s)...", settings.environment)

    # A broken database must be loud: serving requests without tables only
    # produces confusing errors later.
    init_db()

    if check_database_connection():
        logger.info("PostgreSQL: connected")
    else:
        logger.error("PostgreSQL: connection failed")

    yield

    logger.info("TouchGrass backend shutting down...")


app = FastAPI(
    title="TouchGrass API",
    description="Personalized real-world activity agent",
    version="1.1.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
#
# Set CORS_ORIGINS to your deployed frontend URL(s), comma separated, e.g.
#   CORS_ORIGINS=https://touchgrass.vercel.app
# Optional CORS_ORIGIN_REGEX allows Vercel preview URLs, e.g.
#   CORS_ORIGIN_REGEX=https://touchgrass-.*\.vercel\.app
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ERROR HANDLING
#
# Any unexpected error returns clean JSON (never a stack trace),
# and the CORS middleware still adds its headers to it.
# ============================================================

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)

    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong. Please try again."},
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
    database_ok = check_database_connection()

    return {
        "status": "healthy" if database_ok else "degraded",
        "database": "connected" if database_ok else "disconnected",
    }

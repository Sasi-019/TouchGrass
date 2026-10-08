from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from . import models

from .routers.auth import router as auth_router
from .routers.profile import router as profile_router
from .routers.activities import router as activities_router
from .routers.agent import router as agent_router


app = FastAPI(title="TouchGrass API")


# -------------------------
# CORS
# -------------------------

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


# -------------------------
# Routers
# -------------------------

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(activities_router)
app.include_router(agent_router)


# -------------------------
# Database
# -------------------------

Base.metadata.create_all(bind=engine)


# -------------------------
# Basic routes
# -------------------------

@app.get("/")
def root():
    return {"message": "TouchGrass backend is running"}


@app.get("/db-test")
def database_test():
    return {"message": "Database connection is configured"}
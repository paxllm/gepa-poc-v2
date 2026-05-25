"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.database import init_db
from backend.core.encoding import ensure_utf8_environment

ensure_utf8_environment()
from backend.routes import (
    config,
    core_values,
    costs,
    jobs,
    optimization,
    resumes,
    scoring,
    seed_prompts,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Resume GEPA",
    description="Self-learning hiring intelligence system using GEPA prompt optimization",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(config.router)
app.include_router(jobs.router)
app.include_router(core_values.router)
app.include_router(resumes.router)
app.include_router(optimization.router)
app.include_router(scoring.router)
app.include_router(seed_prompts.router)
app.include_router(costs.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "resume-gepa"}

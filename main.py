"""
Application entrypoint.

Run with:  uvicorn main:app --reload
Then open: http://127.0.0.1:8000/docs   (interactive API docs)
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import activities, auth, coach, dashboard, meals, profile, water, weights
from app.db.database import Base, engine
from app.db.migrations import upgrade_schema
from app.models import activity, meal, profile as profile_model, user, water as water_model, weight

# Creates tables based on our models if they don't exist yet.
# NOTE: This is fine for early development. Once the schema stabilizes,
# we'll switch to Alembic migrations instead of this (I'll explain why
# when we get there — short version: this approach can't handle changes
# to existing tables, only creating new ones).
Base.metadata.create_all(bind=engine)
upgrade_schema(engine)

app = FastAPI(
    title="NutriTrack AI",
    description="AI-powered nutrition and health assistant API",
    version="0.1.0",
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(activities.router)
app.include_router(meals.router)
app.include_router(water.router)
app.include_router(weights.router)
app.include_router(dashboard.router)
app.include_router(coach.router)

FRONTEND_DIR = Path(__file__).parent / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def root():
    return FileResponse(FRONTEND_DIR / "index.html")

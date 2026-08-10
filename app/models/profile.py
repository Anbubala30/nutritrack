from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    gender: Mapped[str | None] = mapped_column(String, nullable=True)
    goal_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    dietary_preference: Mapped[str] = mapped_column(String, default="no_preference", nullable=False)
    allergies: Mapped[str | None] = mapped_column(String, nullable=True)
    activity_level: Mapped[str] = mapped_column(String, default="moderately_active", nullable=False)
    goal: Mapped[str] = mapped_column(String, default="maintain", nullable=False)
    calorie_goal: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    protein_goal_g: Mapped[float] = mapped_column(Float, default=120, nullable=False)
    water_goal_ml: Mapped[int] = mapped_column(Integer, default=2500, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

"""
User table definition.

This is the ORM model — it maps directly to the `users` table in the
database. Note it includes `hashed_password`, which we will NEVER expose
through the API (see app/schemas/user.py for the difference).
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Profile fields (age, height, weight, etc.) will be added in the
    # Profile feature, likely as a separate related table rather than
    # crammed into this one — we'll cover why (normalization) when we
    # get there.

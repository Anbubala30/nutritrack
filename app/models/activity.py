from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    activity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    calories_burned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    logged_on: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

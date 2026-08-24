from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.activity import ActivityLog
from app.models.meal import Meal
from app.models.user import User
from app.models.water import WaterLog
from app.schemas.analytics import WeeklyDaySummary, WeeklySummaryResponse

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _day_key(value: date | str) -> str:
    return value.isoformat() if isinstance(value, date) else str(value)


@router.get("/week", response_model=WeeklySummaryResponse)
def weekly_summary(
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    end_date = end_date or date.today()
    start_date = end_date - timedelta(days=6)
    meal_day = func.date(Meal.logged_at).label("logged_on")

    meal_rows = (
        db.query(
            meal_day,
            func.coalesce(func.sum(Meal.calories), 0),
            func.coalesce(func.sum(Meal.protein_g), 0),
        )
        .filter(
            Meal.user_id == current_user.id,
            Meal.logged_at >= start_date,
            Meal.logged_at < end_date + timedelta(days=1),
        )
        .group_by(meal_day)
        .all()
    )
    water_rows = (
        db.query(WaterLog.logged_on, WaterLog.amount_ml)
        .filter(
            WaterLog.user_id == current_user.id,
            WaterLog.logged_on >= start_date,
            WaterLog.logged_on <= end_date,
        )
        .all()
    )
    activity_rows = (
        db.query(
            ActivityLog.logged_on,
            func.coalesce(func.sum(ActivityLog.minutes), 0),
            func.coalesce(func.sum(ActivityLog.calories_burned), 0),
        )
        .filter(
            ActivityLog.user_id == current_user.id,
            ActivityLog.logged_on >= start_date,
            ActivityLog.logged_on <= end_date,
        )
        .group_by(ActivityLog.logged_on)
        .all()
    )

    meal_by_day = {
        _day_key(row[0]): {"calories": int(row[1]), "protein_g": round(float(row[2]), 1)}
        for row in meal_rows
    }
    water_by_day = {_day_key(row[0]): int(row[1]) for row in water_rows}
    activity_by_day = {
        _day_key(row[0]): {"minutes": int(row[1]), "calories_burned": int(row[2])}
        for row in activity_rows
    }

    days = []
    for offset in range(7):
        day = start_date + timedelta(days=offset)
        key = day.isoformat()
        meal = meal_by_day.get(key, {})
        activity = activity_by_day.get(key, {})
        days.append(
            WeeklyDaySummary(
                logged_on=day,
                calories=meal.get("calories", 0),
                protein_g=meal.get("protein_g", 0),
                water_ml=water_by_day.get(key, 0),
                activity_minutes=activity.get("minutes", 0),
                calories_burned=activity.get("calories_burned", 0),
            )
        )

    return WeeklySummaryResponse(
        days=days,
        average_calories=round(sum(day.calories for day in days) / len(days)),
        average_water_ml=round(sum(day.water_ml for day in days) / len(days)),
        total_activity_minutes=sum(day.activity_minutes for day in days),
        total_calories_burned=sum(day.calories_burned for day in days),
    )

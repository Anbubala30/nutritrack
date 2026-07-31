from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.meals import meals_for_day
from app.db.database import get_db
from app.models.profile import UserProfile
from app.models.user import User
from app.models.water import WaterLog
from app.schemas.dashboard import DailyDashboard, DailyGoals, NutritionTotals, WaterSummary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

DEFAULT_CALORIE_GOAL = 2000
DEFAULT_PROTEIN_GOAL_G = 120
DEFAULT_WATER_GOAL_ML = 2500


@router.get("", response_model=DailyDashboard)
def read_dashboard(
    logged_on: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logged_on = logged_on or date.today()
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    meals = meals_for_day(db, current_user.id, logged_on)
    water_log = (
        db.query(WaterLog)
        .filter(WaterLog.user_id == current_user.id, WaterLog.logged_on == logged_on)
        .first()
    )

    totals = NutritionTotals(
        calories=sum(meal.calories for meal in meals),
        protein_g=round(sum(meal.protein_g for meal in meals), 1),
        carbs_g=round(sum(meal.carbs_g for meal in meals), 1),
        fat_g=round(sum(meal.fat_g for meal in meals), 1),
    )
    goals = DailyGoals(
        calorie_goal=profile.calorie_goal if profile else DEFAULT_CALORIE_GOAL,
        protein_goal_g=profile.protein_goal_g if profile else DEFAULT_PROTEIN_GOAL_G,
        water_goal_ml=profile.water_goal_ml if profile else DEFAULT_WATER_GOAL_ML,
    )

    return DailyDashboard(
        logged_on=logged_on,
        profile_complete=profile is not None,
        goals=goals,
        totals=totals,
        water=WaterSummary(amount_ml=water_log.amount_ml if water_log else 0, goal_ml=goals.water_goal_ml),
        meals=meals,
    )

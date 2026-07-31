from datetime import date, datetime, time, timedelta
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.meal import Meal
from app.models.profile import UserProfile
from app.models.user import User
from app.models.water import WaterLog
from app.schemas.coach import CalorieRange, CoachResponse, MacroGuidance

router = APIRouter(prefix="/api/coach", tags=["coach"])

ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
}
DISCLAIMER = (
    "Educational estimate for adults only, not medical advice. Pregnancy, breastfeeding, "
    "medical conditions, medications, eating disorders, and major weight changes need "
    "personalized guidance from a qualified clinician or dietitian."
)


def rounded_range(first: float, second: float) -> CalorieRange:
    return CalorieRange(low=round(min(first, second)), high=round(max(first, second)))


def day_totals(db: Session, user_id: int, logged_on: date) -> tuple[int, float, float, float, int]:
    start = datetime.combine(logged_on, time.min)
    end = start + timedelta(days=1)
    meals = (
        db.query(Meal)
        .filter(Meal.user_id == user_id, Meal.logged_at >= start, Meal.logged_at < end)
        .all()
    )
    water = (
        db.query(WaterLog)
        .filter(WaterLog.user_id == user_id, WaterLog.logged_on == logged_on)
        .first()
    )
    return (
        sum(meal.calories for meal in meals),
        sum(meal.protein_g for meal in meals),
        sum(meal.carbs_g for meal in meals),
        sum(meal.fat_g for meal in meals),
        water.amount_ml if water else 0,
    )


@router.get("", response_model=CoachResponse)
def read_coach(
    sex_for_equation: Literal["female", "male", "show_range"] = "show_range",
    logged_on: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logged_on = logged_on or date.today()
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    current_calories, current_protein, current_carbs, current_fat, current_water = day_totals(
        db, current_user.id, logged_on
    )

    required = {
        "age": profile.age if profile else None,
        "height": profile.height_cm if profile else None,
        "weight": profile.weight_kg if profile else None,
    }
    missing_fields = [name for name, value in required.items() if value is None]
    if missing_fields:
        return CoachResponse(
            ready=False,
            logged_on=logged_on,
            missing_fields=missing_fields,
            messages=["Add your age, height, and weight in My plan to create a personal estimate."],
            disclaimer=DISCLAIMER,
            current_calories=current_calories,
            current_water_ml=current_water,
        )

    if profile.age < 18:
        return CoachResponse(
            ready=False,
            logged_on=logged_on,
            messages=["This coach is designed for adults. A clinician or dietitian can help set an appropriate plan for younger people."],
            disclaimer=DISCLAIMER,
            current_calories=current_calories,
            current_water_ml=current_water,
        )

    female_bmr = 9.99 * profile.weight_kg + 6.25 * profile.height_cm - 4.92 * profile.age - 161
    male_bmr = 9.99 * profile.weight_kg + 6.25 * profile.height_cm - 4.92 * profile.age + 5
    if sex_for_equation == "female":
        bmr = CalorieRange(low=round(female_bmr), high=round(female_bmr))
    elif sex_for_equation == "male":
        bmr = CalorieRange(low=round(male_bmr), high=round(male_bmr))
    else:
        bmr = rounded_range(female_bmr, male_bmr)

    activity_factor = ACTIVITY_FACTORS[profile.activity_level]
    maintenance = rounded_range(bmr.low * activity_factor, bmr.high * activity_factor)
    if profile.goal == "lose_weight":
        goal_calories = rounded_range(max(1000, maintenance.low - 500), max(1000, maintenance.high - 500))
        goal_message = "For weight loss, this starts about 500 kcal below estimated maintenance. Review the trend over several weeks instead of expecting a fixed weekly result."
    elif profile.goal == "build_muscle":
        goal_calories = rounded_range(maintenance.low + 250, maintenance.high + 250)
        goal_message = "For weight gain, this starts about 250 kcal above estimated maintenance. Adjust gradually using your weight trend, training, and recovery."
    else:
        goal_calories = maintenance
        goal_message = "For maintenance, this uses your estimated daily energy range. Adjust gradually if your weight trend changes."

    target_midpoint = (goal_calories.low + goal_calories.high) / 2
    macro_guidance = MacroGuidance(
        protein_goal_g=profile.protein_goal_g,
        protein_logged_g=round(current_protein, 1),
        carbohydrate_range_g=rounded_range(target_midpoint * 0.45 / 4, target_midpoint * 0.65 / 4),
        fat_range_g=rounded_range(target_midpoint * 0.20 / 9, target_midpoint * 0.35 / 9),
    )

    messages = [goal_message]
    calorie_gap = profile.calorie_goal - current_calories
    if calorie_gap > 0:
        messages.append(f"Your saved plan has {calorie_gap:,} kcal remaining for this day.")
    else:
        messages.append(f"Your saved plan is {abs(calorie_gap):,} kcal above its calorie target today.")

    protein_gap = profile.protein_goal_g - current_protein
    if protein_gap > 0:
        messages.append(f"You have {round(protein_gap, 1)} g of protein left to reach your saved protein target.")
    else:
        messages.append("You have reached your saved protein target for this day.")

    if current_water < profile.water_goal_ml:
        messages.append(f"Water is {profile.water_goal_ml - current_water:,} ml below your saved daily target.")
    else:
        messages.append("You have reached your saved water target for this day.")

    return CoachResponse(
        ready=True,
        logged_on=logged_on,
        messages=messages,
        disclaimer=DISCLAIMER,
        method="Mifflin-St Jeor resting-energy estimate with an activity adjustment.",
        bmr_calories=bmr,
        maintenance_calories=maintenance,
        goal_calories=goal_calories,
        macro_guidance=macro_guidance,
        current_calories=current_calories,
        current_water_ml=current_water,
    )

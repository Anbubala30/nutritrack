from datetime import date

from pydantic import BaseModel

from app.schemas.meal import MealResponse


class NutritionTotals(BaseModel):
    calories: int = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0


class DailyGoals(BaseModel):
    calorie_goal: int
    protein_goal_g: float
    water_goal_ml: int


class WaterSummary(BaseModel):
    amount_ml: int
    goal_ml: int


class DailyDashboard(BaseModel):
    logged_on: date
    profile_complete: bool
    goals: DailyGoals
    totals: NutritionTotals
    water: WaterSummary
    meals: list[MealResponse]

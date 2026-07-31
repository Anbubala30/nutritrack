from datetime import date

from pydantic import BaseModel


class CalorieRange(BaseModel):
    low: int
    high: int


class MacroGuidance(BaseModel):
    protein_goal_g: float
    protein_logged_g: float
    carbohydrate_range_g: CalorieRange
    fat_range_g: CalorieRange


class CoachResponse(BaseModel):
    ready: bool
    logged_on: date
    missing_fields: list[str] = []
    messages: list[str]
    disclaimer: str
    method: str | None = None
    bmr_calories: CalorieRange | None = None
    maintenance_calories: CalorieRange | None = None
    goal_calories: CalorieRange | None = None
    macro_guidance: MacroGuidance | None = None
    current_calories: int = 0
    current_water_ml: int = 0

from datetime import date

from pydantic import BaseModel


class WeeklyDaySummary(BaseModel):
    logged_on: date
    calories: int = 0
    protein_g: float = 0
    water_ml: int = 0
    activity_minutes: int = 0
    calories_burned: int = 0


class WeeklySummaryResponse(BaseModel):
    days: list[WeeklyDaySummary]
    average_calories: int
    average_water_ml: int
    total_activity_minutes: int
    total_calories_burned: int

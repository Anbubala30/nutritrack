from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.meal import MealType


class PlannedMealCreate(BaseModel):
    planned_for: date
    name: str = Field(min_length=1, max_length=120)
    meal_type: MealType
    calories: int = Field(ge=0, le=5000)
    protein_g: float = Field(default=0, ge=0, le=500)
    carbs_g: float = Field(default=0, ge=0, le=1000)
    fat_g: float = Field(default=0, ge=0, le=500)


class PlannedMealResponse(PlannedMealCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MealType = Literal["breakfast", "lunch", "dinner", "snack"]


class MealCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    meal_type: MealType
    calories: int = Field(ge=0, le=5000)
    protein_g: float = Field(default=0, ge=0, le=500)
    carbs_g: float = Field(default=0, ge=0, le=1000)
    fat_g: float = Field(default=0, ge=0, le=500)
    logged_at: datetime | None = None


class MealResponse(MealCreate):
    id: int
    logged_at: datetime

    model_config = ConfigDict(from_attributes=True)

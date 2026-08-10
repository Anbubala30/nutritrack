from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ActivityLevel = Literal["sedentary", "lightly_active", "moderately_active", "very_active"]
HealthGoal = Literal["lose_weight", "maintain", "build_muscle"]
Gender = Literal["female", "male", "nonbinary", "prefer_not_to_say"]
DietaryPreference = Literal["no_preference", "vegetarian", "vegan", "pescatarian", "halal", "kosher", "other"]


class ProfileUpdate(BaseModel):
    age: int | None = Field(default=None, ge=13, le=120)
    height_cm: float | None = Field(default=None, ge=80, le=260)
    weight_kg: float | None = Field(default=None, ge=25, le=400)
    gender: Gender | None = None
    goal_weight_kg: float | None = Field(default=None, ge=25, le=400)
    dietary_preference: DietaryPreference = "no_preference"
    allergies: str | None = Field(default=None, max_length=500)
    activity_level: ActivityLevel = "moderately_active"
    goal: HealthGoal = "maintain"
    calorie_goal: int = Field(default=2000, ge=800, le=10000)
    protein_goal_g: float = Field(default=120, ge=20, le=500)
    water_goal_ml: int = Field(default=2500, ge=500, le=10000)


class ProfileResponse(ProfileUpdate):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)

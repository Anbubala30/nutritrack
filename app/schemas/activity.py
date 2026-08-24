from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ActivityLogCreate(BaseModel):
    activity_type: str = Field(min_length=1, max_length=80)
    minutes: int = Field(ge=1, le=720)
    calories_burned: int = Field(default=0, ge=0, le=10000)
    logged_on: date
    note: str | None = Field(default=None, max_length=300)


class ActivityLogResponse(ActivityLogCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ActivityDayResponse(BaseModel):
    entries: list[ActivityLogResponse]
    total_minutes: int
    total_calories_burned: int

from datetime import date

from pydantic import BaseModel, Field


class WaterUpdate(BaseModel):
    amount_ml: int = Field(ge=0, le=15000)


class WaterResponse(BaseModel):
    logged_on: date
    amount_ml: int
    goal_ml: int

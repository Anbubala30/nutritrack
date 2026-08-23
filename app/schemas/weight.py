from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class WeightLogUpsert(BaseModel):
    weight_kg: float = Field(ge=25, le=400)
    logged_on: date
    note: str | None = Field(default=None, max_length=300)


class WeightLogResponse(WeightLogUpsert):
    id: int

    model_config = ConfigDict(from_attributes=True)


class WeightHistoryResponse(BaseModel):
    entries: list[WeightLogResponse]
    bmi: float | None = None
    bmi_note: str

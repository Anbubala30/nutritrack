from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.profile import UserProfile
from app.models.user import User
from app.models.weight import WeightLog
from app.schemas.weight import WeightHistoryResponse, WeightLogResponse, WeightLogUpsert

router = APIRouter(prefix="/api/weights", tags=["weights"])


@router.get("", response_model=WeightHistoryResponse)
def list_weight_logs(
    days: int = 90,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    days = min(max(days, 7), 365)
    entries = (
        db.query(WeightLog)
        .filter(
            WeightLog.user_id == current_user.id,
            WeightLog.logged_on >= date.today() - timedelta(days=days - 1),
        )
        .order_by(WeightLog.logged_on.desc())
        .all()
    )
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    bmi = None
    if entries and profile and profile.height_cm:
        bmi = round(entries[0].weight_kg / (profile.height_cm / 100) ** 2, 1)

    return WeightHistoryResponse(
        entries=entries,
        bmi=bmi,
        bmi_note=(
            "BMI is a screening measure, not a diagnosis."
            if bmi is not None
            else "Add your height in My plan to calculate BMI."
        ),
    )


@router.put("", response_model=WeightLogResponse)
def save_weight_log(
    weight_in: WeightLogUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = (
        db.query(WeightLog)
        .filter(WeightLog.user_id == current_user.id, WeightLog.logged_on == weight_in.logged_on)
        .first()
    )
    if entry is None:
        entry = WeightLog(user_id=current_user.id, **weight_in.model_dump())
        db.add(entry)
    else:
        entry.weight_kg = weight_in.weight_kg
        entry.note = weight_in.note

    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_weight_log(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = (
        db.query(WeightLog)
        .filter(WeightLog.id == entry_id, WeightLog.user_id == current_user.id)
        .first()
    )
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weight entry not found.")
    db.delete(entry)
    db.commit()

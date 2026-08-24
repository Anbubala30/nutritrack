from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.activity import ActivityLog
from app.models.user import User
from app.schemas.activity import ActivityDayResponse, ActivityLogCreate, ActivityLogResponse

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("", response_model=ActivityDayResponse)
def list_activities(
    logged_on: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entries = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == current_user.id, ActivityLog.logged_on == logged_on)
        .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
        .all()
    )
    totals = (
        db.query(
            func.coalesce(func.sum(ActivityLog.minutes), 0),
            func.coalesce(func.sum(ActivityLog.calories_burned), 0),
        )
        .filter(ActivityLog.user_id == current_user.id, ActivityLog.logged_on == logged_on)
        .one()
    )
    return ActivityDayResponse(
        entries=entries,
        total_minutes=int(totals[0]),
        total_calories_burned=int(totals[1]),
    )


@router.post("", response_model=ActivityLogResponse, status_code=status.HTTP_201_CREATED)
def create_activity(
    activity_in: ActivityLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = ActivityLog(user_id=current_user.id, **activity_in.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = (
        db.query(ActivityLog)
        .filter(ActivityLog.id == entry_id, ActivityLog.user_id == current_user.id)
        .first()
    )
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity entry not found.")
    db.delete(entry)
    db.commit()

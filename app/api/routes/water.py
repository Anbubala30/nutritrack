from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.dashboard import DEFAULT_WATER_GOAL_ML
from app.db.database import get_db
from app.models.profile import UserProfile
from app.models.user import User
from app.models.water import WaterLog
from app.schemas.water import WaterResponse, WaterUpdate

router = APIRouter(prefix="/api/water", tags=["water"])


@router.put("", response_model=WaterResponse)
def set_water(
    water_in: WaterUpdate,
    logged_on: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logged_on = logged_on or date.today()
    water_log = (
        db.query(WaterLog)
        .filter(WaterLog.user_id == current_user.id, WaterLog.logged_on == logged_on)
        .first()
    )
    if water_log is None:
        water_log = WaterLog(
            user_id=current_user.id,
            logged_on=logged_on,
            amount_ml=water_in.amount_ml,
        )
        db.add(water_log)
    else:
        water_log.amount_ml = water_in.amount_ml

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    db.commit()
    return WaterResponse(
        logged_on=logged_on,
        amount_ml=water_log.amount_ml,
        goal_ml=profile.water_goal_ml if profile else DEFAULT_WATER_GOAL_ML,
    )

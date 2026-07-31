from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.meal import Meal
from app.models.user import User
from app.schemas.meal import MealCreate, MealResponse

router = APIRouter(prefix="/api/meals", tags=["meals"])


def meals_for_day(db: Session, user_id: int, logged_on: date) -> list[Meal]:
    start = datetime.combine(logged_on, time.min)
    end = start + timedelta(days=1)
    return (
        db.query(Meal)
        .filter(Meal.user_id == user_id, Meal.logged_at >= start, Meal.logged_at < end)
        .order_by(Meal.logged_at.desc())
        .all()
    )


@router.get("", response_model=list[MealResponse])
def list_meals(
    logged_on: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return meals_for_day(db, current_user.id, logged_on or date.today())


@router.post("", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
def add_meal(
    meal_in: MealCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meal = Meal(
        user_id=current_user.id,
        **meal_in.model_dump(exclude={"logged_at"}),
        logged_at=meal_in.logged_at or datetime.now(timezone.utc),
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(
    meal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meal = (
        db.query(Meal)
        .filter(Meal.id == meal_id, Meal.user_id == current_user.id)
        .first()
    )
    if meal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found.")

    db.delete(meal)
    db.commit()

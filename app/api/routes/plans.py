from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.meal import Meal
from app.models.planned_meal import PlannedMeal
from app.models.user import User
from app.schemas.meal import MealResponse
from app.schemas.planner import PlannedMealCreate, PlannedMealResponse

router = APIRouter(prefix="/api/plans", tags=["plans"])


@router.get("", response_model=list[PlannedMealResponse])
def list_planned_meals(
    planned_for: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_day = planned_for or date.today()
    return (
        db.query(PlannedMeal)
        .filter(
            PlannedMeal.user_id == current_user.id,
            PlannedMeal.planned_for == target_day,
        )
        .order_by(PlannedMeal.meal_type, PlannedMeal.created_at)
        .all()
    )


@router.post("", response_model=PlannedMealResponse, status_code=status.HTTP_201_CREATED)
def add_planned_meal(
    meal_in: PlannedMealCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    planned_meal = PlannedMeal(user_id=current_user.id, **meal_in.model_dump())
    db.add(planned_meal)
    db.commit()
    db.refresh(planned_meal)
    return planned_meal


@router.post("/{planned_meal_id}/log", response_model=MealResponse)
def log_planned_meal(
    planned_meal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    planned_meal = (
        db.query(PlannedMeal)
        .filter(PlannedMeal.id == planned_meal_id, PlannedMeal.user_id == current_user.id)
        .first()
    )
    if planned_meal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planned meal not found.")

    meal = Meal(
        user_id=current_user.id,
        name=planned_meal.name,
        meal_type=planned_meal.meal_type,
        calories=planned_meal.calories,
        protein_g=planned_meal.protein_g,
        carbs_g=planned_meal.carbs_g,
        fat_g=planned_meal.fat_g,
        logged_at=datetime.now(timezone.utc),
    )
    db.add(meal)
    db.delete(planned_meal)
    db.commit()
    db.refresh(meal)
    return meal


@router.delete("/{planned_meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_planned_meal(
    planned_meal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    planned_meal = (
        db.query(PlannedMeal)
        .filter(PlannedMeal.id == planned_meal_id, PlannedMeal.user_id == current_user.id)
        .first()
    )
    if planned_meal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planned meal not found.")
    db.delete(planned_meal)
    db.commit()

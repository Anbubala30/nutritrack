from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.custom_food import CustomFood
from app.models.user import User
from app.schemas.meal import CustomFoodCreate, CustomFoodResponse

router = APIRouter(prefix="/api/foods", tags=["foods"])


@router.get("", response_model=list[CustomFoodResponse])
def list_custom_foods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(CustomFood)
        .filter(CustomFood.user_id == current_user.id)
        .order_by(CustomFood.name.asc())
        .all()
    )


@router.post("", response_model=CustomFoodResponse, status_code=status.HTTP_201_CREATED)
def create_custom_food(
    food_in: CustomFoodCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing_food = (
        db.query(CustomFood)
        .filter(CustomFood.user_id == current_user.id, CustomFood.name == food_in.name)
        .first()
    )
    if existing_food:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A saved food with that name already exists.",
        )

    food = CustomFood(user_id=current_user.id, **food_in.model_dump())
    db.add(food)
    db.commit()
    db.refresh(food)
    return food


@router.delete("/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_custom_food(
    food_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    food = (
        db.query(CustomFood)
        .filter(CustomFood.id == food_id, CustomFood.user_id == current_user.id)
        .first()
    )
    if food is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved food not found.")
    db.delete(food)
    db.commit()

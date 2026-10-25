import asyncio
import base64
import json
import re
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from openai import OpenAI
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.models.meal import Meal
from app.models.user import User
from app.schemas.meal import FoodPhotoEstimate, MealCreate, MealResponse, MealSuggestion

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


@router.get("/suggestions", response_model=list[MealSuggestion])
def recent_meal_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recent_meals = (
        db.query(Meal)
        .filter(Meal.user_id == current_user.id)
        .order_by(Meal.logged_at.desc())
        .limit(60)
        .all()
    )
    suggestions = []
    used_names = set()
    for meal in recent_meals:
        normalized_name = meal.name.strip().casefold()
        if not normalized_name or normalized_name in used_names:
            continue
        used_names.add(normalized_name)
        suggestions.append(
            MealSuggestion(
                name=meal.name,
                meal_type=meal.meal_type,
                calories=meal.calories,
                protein_g=meal.protein_g,
                carbs_g=meal.carbs_g,
                fat_g=meal.fat_g,
            )
        )
        if len(suggestions) == 6:
            break
    return suggestions


@router.post("/analyze-photo", response_model=FoodPhotoEstimate)
async def analyze_food_photo(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    del current_user  # Authentication is required even though photos are not stored.
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Food photo analysis is not configured yet. Add OPENAI_API_KEY in the service environment settings.",
        )
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Choose a JPG, PNG, or WEBP food photo.",
        )

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The photo file is empty.")
    if len(image_bytes) > 8 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Choose a photo smaller than 8 MB.",
        )

    data_url = f"data:{image.content_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    prompt = (
        "Analyze this food photo and estimate one combined meal. Return only a JSON object with "
        "name, meal_type, calories, protein_g, carbs_g, fat_g, confidence, and note. "
        "meal_type must be breakfast, lunch, dinner, or snack. confidence must be low, medium, or high. "
        "Use conservative estimates, say what is uncertain in note, and do not make medical claims."
    )
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = await asyncio.to_thread(
            client.responses.create,
            model=settings.OPENAI_VISION_MODEL,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url, "detail": "low"},
                    ],
                }
            ],
        )
        output = response.output_text.strip()
        json_match = re.search(r"\{.*\}", output, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object was returned.")
        return FoodPhotoEstimate.model_validate(json.loads(json_match.group(0)))
    except Exception as error:
        if isinstance(error, (json.JSONDecodeError, ValueError)):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="I could not make a reliable estimate from that photo. Try a clearer food photo.",
            ) from error
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Food photo analysis is temporarily unavailable. Try again shortly.",
        ) from error


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

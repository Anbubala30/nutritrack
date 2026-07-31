"""
Pydantic schemas — these define what data looks like at the API boundary
(what clients send us, what we send back). They are intentionally separate
from app/models/user.py (the database table).

Naming convention used here (common in FastAPI projects):
  - UserCreate:   what the client sends to register
  - UserLogin:    what the client sends to log in
  - UserResponse: what we send back (never includes the password/hash)
  - Token:        what we send back after a successful login
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None

    # Lets Pydantic read data straight off a SQLAlchemy object's
    # attributes (model.email, model.id, ...) instead of requiring a dict.
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

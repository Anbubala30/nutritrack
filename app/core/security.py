"""
Security utilities: password hashing and JWT tokens.

Why we hash passwords: if the database is ever leaked, plaintext passwords
would compromise every user's account (and likely their other accounts too,
since people reuse passwords). Hashing is one-way — we can check a password
is correct without ever storing or being able to recover the original.

We use bcrypt via passlib. bcrypt is deliberately slow (it has a "cost factor"),
which makes brute-force attacks on stolen hashes much harder.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.core.config import settings

def hash_password(plain_password: str) -> str:
    """Turn a plaintext password into a bcrypt hash for storage."""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a login attempt's password against the stored hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str) -> str:
    """
    Create a signed JWT for a logged-in user.

    `subject` is typically the user's ID or email — whatever we want to
    identify them by on future requests. The token is signed with our
    SECRET_KEY, so we can trust it wasn't tampered with, without needing
    to look up a session in the database on every request.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """
    Decode a JWT and return the subject (user identifier), or None if
    the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except jwt.JWTError:
        return None

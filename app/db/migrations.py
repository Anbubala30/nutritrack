"""Lightweight additive schema upgrades for the early NutriTrack project.

Alembic will replace this helper once the schema grows beyond simple additions.
"""

from sqlalchemy import Engine, inspect, text

PROFILE_COLUMNS = {
    "gender": "VARCHAR",
    "goal_weight_kg": "FLOAT",
    "dietary_preference": "VARCHAR",
    "allergies": "VARCHAR",
}


def upgrade_schema(engine: Engine) -> None:
    """Add profile columns that are safe to introduce without losing data."""
    inspector = inspect(engine)
    if not inspector.has_table("user_profiles"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("user_profiles")}
    with engine.begin() as connection:
        for column_name, column_type in PROFILE_COLUMNS.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE user_profiles ADD COLUMN {column_name} {column_type}")
                )

"""Add the optional account_users.height_cm column to an existing database."""

from sqlalchemy import inspect, text

from app.database import engine


def migrate() -> bool:
    columns = {column["name"] for column in inspect(engine).get_columns("account_users")}
    if "height_cm" in columns:
        return False
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE account_users ADD COLUMN height_cm FLOAT"))
    return True


if __name__ == "__main__":
    changed = migrate()
    print("height_cm added" if changed else "height_cm already exists")

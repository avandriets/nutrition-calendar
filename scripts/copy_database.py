"""Copy application data between two already migrated databases.

The target must be empty. Schema creation and upgrades remain Alembic's job.
"""

import argparse
import os

from sqlalchemy import create_engine, func, select

from app.database import Base

# Register every table in Base.metadata.
from app.accounts import model as accounts_model  # noqa: F401,E402
from app.meals import model as meals_model  # noqa: F401,E402
from app.products import model as products_model  # noqa: F401,E402
from app.users import model as users_model  # noqa: F401,E402


TABLE_ORDER = (
    "accounts",
    "products",
    "account_users",
    "user_goals",
    "body_measurements",
    "meals",
    "meal_rows",
    "meal_entries",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy all application rows to an empty migrated database."
    )
    parser.add_argument(
        "--source-url",
        default=os.getenv("SOURCE_DATABASE_URL", "sqlite:///./backend.db"),
        help="Source SQLAlchemy URL (or SOURCE_DATABASE_URL).",
    )
    parser.add_argument(
        "--target-url",
        default=os.getenv("TARGET_DATABASE_URL"),
        help="Target SQLAlchemy URL (or TARGET_DATABASE_URL).",
    )
    args = parser.parse_args()
    if not args.target_url:
        parser.error("--target-url or TARGET_DATABASE_URL is required")
    if args.source_url == args.target_url:
        parser.error("source and target URLs must differ")
    return args


def main() -> None:
    args = parse_args()
    source_engine = create_engine(args.source_url, pool_pre_ping=True)
    target_engine = create_engine(args.target_url, pool_pre_ping=True)

    try:
        with source_engine.connect() as source, target_engine.begin() as target:
            nonempty = []
            for table_name in TABLE_ORDER:
                table = Base.metadata.tables[table_name]
                count = target.scalar(select(func.count()).select_from(table))
                if count:
                    nonempty.append(f"{table_name} ({count})")
            if nonempty:
                raise RuntimeError(
                    "Target database is not empty: " + ", ".join(nonempty)
                )

            total = 0
            for table_name in TABLE_ORDER:
                table = Base.metadata.tables[table_name]
                rows = [dict(row._mapping) for row in source.execute(select(table))]
                if rows:
                    target.execute(table.insert(), rows)
                total += len(rows)
                print(f"{table_name}: {len(rows)} rows")

        print(f"Copied {total} rows successfully.")
    finally:
        source_engine.dispose()
        target_engine.dispose()


if __name__ == "__main__":
    main()

import atexit
import os
from pathlib import Path
import tempfile

from alembic import command
from alembic.config import Config


file_descriptor, database_path = tempfile.mkstemp(
    prefix="nutrition-tests-", suffix=".db"
)
os.close(file_descriptor)
os.environ["DATABASE_URL"] = f"sqlite:///{database_path}"

project_root = Path(__file__).resolve().parents[1]
alembic_config = Config(project_root / "alembic.ini")
command.upgrade(alembic_config, "head")


@atexit.register
def remove_test_database() -> None:
    Path(database_path).unlink(missing_ok=True)

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
os.environ.setdefault("AUTH0_DOMAIN", "test.auth0.com")
os.environ.setdefault("AUTH0_AUDIENCE", "https://nutrition-api")

project_root = Path(__file__).resolve().parents[1]
alembic_config = Config(project_root / "alembic.ini")
command.upgrade(alembic_config, "head")

from app.auth import require_auth  # noqa: E402
from app.main import app  # noqa: E402

app.dependency_overrides[require_auth] = lambda: {"sub": "auth0|test-user"}


@atexit.register
def remove_test_database() -> None:
    Path(database_path).unlink(missing_ok=True)

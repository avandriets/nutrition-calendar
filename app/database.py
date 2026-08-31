import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./backend.db")

is_sqlite = DATABASE_URL.startswith("sqlite")
engine_options = {
    "pool_pre_ping": True,
}
if is_sqlite:
    engine_options["connect_args"] = {"check_same_thread": False}
else:
    # Recycle connections before common managed-MySQL/MariaDB idle timeouts.
    engine_options["pool_recycle"] = int(os.getenv("DB_POOL_RECYCLE_SECONDS", "1800"))

engine = create_engine(DATABASE_URL, **engine_options)

if is_sqlite:
    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

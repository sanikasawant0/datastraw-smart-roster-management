
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Store the database in the project root
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "roster.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for database models
class Base(DeclarativeBase):
    pass


# Dependency for database sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from typing import Generator
from app.db.database import SessionLocal

def get_db() -> Generator:
    """Provides transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

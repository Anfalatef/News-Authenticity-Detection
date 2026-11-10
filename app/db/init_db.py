"""
Database initialization script.

Creates all tables defined in models.py.
"""

from app.db.connection import Base, engine
from app.db import models  # noqa: F401


def init_database() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")


if __name__ == "__main__":
    init_database()

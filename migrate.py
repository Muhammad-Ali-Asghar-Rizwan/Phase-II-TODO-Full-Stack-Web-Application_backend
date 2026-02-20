"""Database migration script to create tables."""

from models import SQLModel
from db import sync_engine


def main():
    """Create all database tables."""
    print("Creating database tables...")
    SQLModel.metadata.create_all(sync_engine)
    print("✓ Database tables created successfully!")


if __name__ == "__main__":
    main()

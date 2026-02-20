"""Better Auth configuration for the backend."""

from better_auth import auth
from better_auth import models
from sqlmodel import SQLModel
from db import get_async_session
from contextlib import asynccontextmanager
from fastapi import FastAPI
import os

# Initialize Better Auth with database configuration
auth_app = auth(
    database_url=os.getenv("DATABASE_URL"),
    secret=os.getenv("BETTER_AUTH_SECRET", "fallback_secret_for_development"),
    # Configure email and password authentication
    email_password_enabled=True,
    # Add any other configurations as needed
    app_name="Todo App",
)
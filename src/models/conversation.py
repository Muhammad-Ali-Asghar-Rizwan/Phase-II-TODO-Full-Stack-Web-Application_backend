from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional
import uuid

class Conversation(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)  # References user ID from existing user model
    title: Optional[str] = Field(default="New Conversation", max_length=255)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional
import uuid

class Message(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    conversation_id: str = Field(index=True, foreign_key="conversation.id")
    role: str = Field(sa_column_kwargs={"comment": "user, assistant, or system"})
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message_metadata: Optional[dict] = Field(default=None, sa_column_kwargs={"comment": "JSON metadata"})
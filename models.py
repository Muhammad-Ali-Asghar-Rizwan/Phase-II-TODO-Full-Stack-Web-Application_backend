"""SQLModel database models for Todo AI Chatbot."""

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String, Text, Boolean, DateTime, Index, JSON
from typing import Optional, List
from datetime import datetime
import uuid


class User(SQLModel, table=True):
    """User table managed by Better Auth."""

    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
    name: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship to tasks
    tasks: List["Task"] = Relationship(back_populates="user")
    conversations: List["Conversation"] = Relationship(back_populates="user")


class Task(SQLModel, table=True):
    """Task entity representing a todo item owned by a user."""

    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=200, nullable=False)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    # Support both 'status' and 'completed' for backward compatibility
    status: str = Field(default="pending", max_length=20)  # pending, completed, archived
    completed: bool = Field(default=False)  # Legacy field for backward compatibility
    due_date: Optional[datetime] = Field(default=None)
    priority: str = Field(default="medium", max_length=20)  # low, medium, high
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship to user
    user: Optional["User"] = Relationship(back_populates="tasks")

    class Config:
        indexes = [
            Index("idx_tasks_user_id", "user_id"),
            Index("idx_tasks_status", "status"),
            Index("idx_tasks_priority", "priority"),
            Index("idx_tasks_due_date", "due_date"),
        ]


class Conversation(SQLModel, table=True):
    """Conversation entity representing a chat session."""

    __tablename__ = "conversations"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: Optional[datetime] = Field(default=None)

    # Relationships
    user: Optional["User"] = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(back_populates="conversation")
    conversation_state: Optional["ConversationState"] = Relationship(back_populates="conversation")

    class Config:
        indexes = [
            Index("idx_conversations_user_id", "user_id"),
            Index("idx_conversations_last_message_at", "last_message_at"),
        ]


class Message(SQLModel, table=True):
    """Message entity representing a chat message in a conversation."""

    __tablename__ = "messages"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    conversation_id: str = Field(foreign_key="conversations.id", index=True)
    role: str = Field(max_length=20)  # user, assistant, system
    content: str = Field(sa_column=Column(Text))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    # Relationship to conversation
    conversation: Optional["Conversation"] = Relationship(back_populates="messages")

    class Config:
        indexes = [
            Index("idx_messages_conversation_id", "conversation_id"),
            Index("idx_messages_timestamp", "timestamp"),
            Index("idx_messages_role", "role"),
        ]


class ConversationState(SQLModel, table=True):
    """ConversationState entity storing the current state of a conversation."""

    __tablename__ = "conversation_states"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    conversation_id: str = Field(foreign_key="conversations.id", unique=True)
    state_data: dict = Field(sa_column=Column(JSON))  # Store state as JSON
    version: int = Field(default=1)

    # Relationship to conversation
    conversation: Optional["Conversation"] = Relationship(back_populates="conversation_state")

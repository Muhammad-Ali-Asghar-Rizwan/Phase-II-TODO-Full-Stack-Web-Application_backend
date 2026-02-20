from sqlmodel import Session, select
from typing import List
from datetime import datetime
from ..models.message import Message


class MessageService:
    def create_message(self, session: Session, conversation_id: str, role: str, content: str, metadata: dict = None) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_metadata=metadata
        )
        session.add(message)
        session.commit()
        session.refresh(message)
        return message

    def get_messages_by_conversation(self, session: Session, conversation_id: str) -> List[Message]:
        query = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.timestamp.asc())
        return session.exec(query).all()

    def get_latest_messages(self, session: Session, conversation_id: str, limit: int = 10) -> List[Message]:
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.desc())
            .limit(limit)
        )
        return session.exec(query).all()

    def get_message(self, session: Session, message_id: str) -> Message | None:
        return session.get(Message, message_id)
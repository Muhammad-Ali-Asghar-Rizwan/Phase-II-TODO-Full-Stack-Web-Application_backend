from datetime import datetime
from sqlmodel import Session, select
from typing import List, Optional
from ..models.conversation import Conversation


class ConversationService:
    def create_conversation(self, session: Session, user_id: str, title: Optional[str] = None) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        return conversation

    def get_user_conversations(self, session: Session, user_id: str, active_only: bool = False) -> List[Conversation]:
        query = select(Conversation).where(Conversation.user_id == user_id)
        if active_only:
            query = query.where(Conversation.is_active == True)
        return session.exec(query).all()

    def get_conversation(self, session: Session, conversation_id: str) -> Conversation | None:
        return session.get(Conversation, conversation_id)

    def update_conversation(self, session: Session, conversation: Conversation) -> Conversation:
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        return conversation

    def deactivate_conversation(self, session: Session, conversation: Conversation) -> Conversation:
        conversation.is_active = False
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        return conversation
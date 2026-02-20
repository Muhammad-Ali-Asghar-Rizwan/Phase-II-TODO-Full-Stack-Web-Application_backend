"""
Chat API Endpoint
Implements the stateless chat endpoint that connects the frontend to the AI agent
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import logging

from ..models.message import Message
from ..models.conversation import Conversation
from ..services.conversation_service import ConversationService
from ..services.message_service import MessageService
from ..tools.task_tools import TaskTools
from ..agents.todo_agent import TodoAgent
from ...database import engine

# Import Better Auth dependencies
from auth import get_current_user  # Assuming this is how Better Auth is integrated

# Set up logging
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/conversation")
async def chat_conversation(
    request: Request,
    message: str,
    conversation_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)  # Authentication check
) -> Dict[str, Any]:
    """
    Initiates a new conversation or continues an existing one.
    This is a stateless endpoint that handles the chat interaction.
    """
    # Get database session
    with Session(engine) as session:
        # Initialize services
        conversation_service = ConversationService()
        message_service = MessageService()
        task_tools = TaskTools(session)
        agent = TodoAgent()
        
        # Get or create conversation
        if conversation_id:
            # Retrieve existing conversation
            conversation = conversation_service.get_conversation(session, conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Verify that the conversation belongs to the current user
            if conversation.user_id != current_user.get("id"):
                raise HTTPException(status_code=403, detail="Access denied")
        else:
            # Create new conversation
            conversation = conversation_service.create_conversation(
                session, 
                user_id=current_user.get("id"),
                title=f"Chatbot Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            conversation_id = conversation.id
        
        # Store the user's message
        user_message = message_service.create_message(
            session,
            conversation_id=conversation_id,
            role="user",
            content=message
        )
        
        # Prepare messages for the AI agent (last N messages for context)
        # In a real implementation, you might want to limit the context window
        all_messages = message_service.get_messages_by_conversation(session, conversation_id)
        chat_history = []
        for msg in all_messages:
            chat_history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add the current user message
        chat_history.append({
            "role": "user",
            "content": message
        })
        
        try:
            # Get response from AI agent
            agent_response = agent.chat(chat_history)
        except Exception as e:
            logger.error(f"Error getting response from AI agent: {str(e)}")
            return {
                "conversation_id": conversation_id,
                "response": "Sorry, I'm having trouble processing your request right now. Please try again.",
                "actions_taken": [],
                "requires_confirmation": False,
                "timestamp": datetime.now().isoformat()
            }
        
        # Process tool calls if any
        import json
        tool_responses = []
        if 'tool_calls' in agent_response.get('choices', [{}])[0]:
            for tool_call in agent_response['choices'][0]['tool_calls']:
                tool_name = tool_call['function']['name']
                try:
                    tool_args = json.loads(tool_call['function']['arguments'])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON arguments for tool call {tool_name}: {tool_call['function']['arguments']}")
                    tool_responses.append({
                        "tool_call_id": tool_call['id'],
                        "output": {"error": "Invalid arguments for tool call", "details": "The arguments provided could not be parsed as valid JSON."}
                    })
                    continue
                
                # Add user_id to tool arguments to ensure proper authorization
                tool_args['owner_id'] = current_user.get("id")
                
                # Call the appropriate tool
                if hasattr(task_tools, tool_name):
                    try:
                        tool_method = getattr(task_tools, tool_name)
                        result = tool_method(**tool_args)
                        
                        # Handle confirmation requests
                        if result.get('requires_confirmation'):
                            return {
                                "conversation_id": conversation_id,
                                "response": result.get('message', 'Confirmation required'),
                                "actions_taken": [],
                                "requires_confirmation": True,
                                "confirm_action": {
                                    "tool_name": tool_name,
                                    "tool_args": tool_args
                                },
                                "timestamp": datetime.now().isoformat()
                            }
                        
                        tool_responses.append({
                            "tool_call_id": tool_call['id'],
                            "output": result
                        })
                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {str(e)}")
                        tool_responses.append({
                            "tool_call_id": tool_call['id'],
                            "output": {
                                "error": f"Error executing {tool_name}",
                                "details": str(e)
                            }
                        })
                else:
                    logger.warning(f"Unknown tool called: {tool_name}")
                    tool_responses.append({
                        "tool_call_id": tool_call['id'],
                        "output": {
                            "error": f"Unknown tool: {tool_name}",
                            "details": "The requested operation is not supported."
                        }
                    })
        
        # Get the final response from the agent after processing tools
        try:
            final_response = agent_response['choices'][0]['message']['content']
        except KeyError:
            logger.warning("AI agent response did not contain expected message content")
            final_response = "I processed your request, but there was an issue generating a response."
        
        # Store the AI's response
        try:
            ai_message = message_service.create_message(
                session,
                conversation_id=conversation_id,
                role="assistant",
                content=final_response
            )
        except Exception as e:
            logger.error(f"Error storing AI response: {str(e)}")
            # Continue execution even if we can't store the message
        
        # Update conversation timestamp
        conversation.updated_at = datetime.now()
        conversation_service.update_conversation(session, conversation)
        
        # Return the response
        return {
            "conversation_id": conversation_id,
            "response": final_response,
            "actions_taken": tool_responses,
            "requires_confirmation": False,
            "timestamp": datetime.now().isoformat()
        }


@router.get("/conversations")
async def get_user_conversations(
    user_id: str,  # This would come from authentication
    page: int = 1,
    limit: int = 20,
    active_only: bool = False
) -> Dict[str, Any]:
    """
    Retrieves a list of user's conversations.
    """
    with Session(engine) as session:
        conversation_service = ConversationService()
        try:
            conversations = conversation_service.get_user_conversations(
                session, 
                user_id, 
                active_only=active_only
            )
        except Exception as e:
            logger.error(f"Error retrieving conversations for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving conversations")
        
        # Paginate results
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_conversations = conversations[start_idx:end_idx]
        
        conversation_list = []
        for conv in paginated_conversations:
            conversation_list.append({
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "is_active": conv.is_active
            })
        
        return {
            "conversations": conversation_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(conversations),
                "has_more": end_idx < len(conversations)
            }
        }


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Retrieves messages for a specific conversation.
    """
    with Session(engine) as session:
        message_service = MessageService()
        try:
            messages = message_service.get_latest_messages(session, conversation_id, limit)
        except Exception as e:
            logger.error(f"Error retrieving messages for conversation {conversation_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving conversation messages")
        
        message_list = []
        for msg in messages:
            message_list.append({
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.message_metadata
            })
        
        return {
            "messages": message_list
        }
"""AI Assistant routes for the Todo Web App."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from middleware.jwt_auth import get_current_user
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from db import get_session
from models import Task
from datetime import datetime
import re


router = APIRouter(prefix="/ai", tags=["ai-assistant"])


class AIRequest(BaseModel):
    message: str
    user_id: str = None


class AIResponse(BaseModel):
    response: str
    user_id: str
    message: str
    task_created: bool = False
    task_id: Optional[int] = None


async def get_ai_response(message: str, user_id: str, session: AsyncSession) -> dict:
    """
    AI response function that can actually create/manage tasks.
    """
    lower_msg = message.lower()
    
    # Check for task creation intent
    create_patterns = [
        r'add.*task.*to\s+(.+)',
        r'create.*task.*to\s+(.+)',
        r'add.*task\s+(.+)',
        r'create.*task\s+(.+)',
        r'new task\s+(.+)',
        r'add\s+(.+)\s+to my tasks',
    ]
    
    for pattern in create_patterns:
        match = re.search(pattern, lower_msg)
        if match:
            task_title = match.group(1).strip()
            # Remove common words at the end
            task_title = re.sub(r'\s*(to my tasks|for me|please|thanks)$', '', task_title).strip()
            
            if task_title:
                # Actually create the task in database
                new_task = Task(
                    user_id=user_id,
                    title=task_title.title(),
                    description=f"Task created via AI assistant",
                    status="pending",
                    completed=False,
                    priority="medium"
                )
                session.add(new_task)
                await session.commit()
                await session.refresh(new_task)
                
                return {
                    "response": f"✓ Task created successfully: '{task_title.title()}'",
                    "task_created": True,
                    "task_id": new_task.id
                }
    
    # Check for task listing intent
    if any(word in lower_msg for word in ['show', 'list', 'view', 'see', 'my tasks']):
        tasks = (await session.exec(
            select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
        )).all()
        
        if not tasks:
            return {"response": "You don't have any tasks yet. Want to add one?"}
        
        task_list = "\n".join([f"{i+1}. {t.title} - {'✓' if t.completed else '○'}" for i, t in enumerate(tasks[:5])])
        return {"response": f"Here are your tasks:\n{task_list}"}
    
    # Check for task completion intent
    complete_match = re.search(r'mark.*task.*#?(\d+).*completed|complete.*task.*#?(\d+)', lower_msg)
    if complete_match:
        task_num = int(complete_match.group(1) or complete_match.group(2))
        tasks = (await session.exec(
            select(Task).where(Task.user_id == user_id).order_by(Task.created_at.asc())
        )).all()
        
        if 0 < task_num <= len(tasks):
            task = tasks[task_num - 1]
            task.completed = True
            task.status = "completed"
            task.updated_at = datetime.utcnow()
            session.add(task)
            await session.commit()
            return {"response": f"✓ Marked task #{task_num} '{task.title}' as completed!"}
        else:
            return {"response": f"Task #{task_num} not found."}
    
    # Check for task deletion intent (multiple patterns)
    delete_patterns = [
        r'delete.*task.*#?(\d+)',
        r'remove.*task.*#?(\d+)',
        r'del.*task.*#?(\d+)',
        r'delete.*#?(\d+)',
        r'remove.*#?(\d+)',
        r'del.*#?(\d+)',
        r'.*task.*del.*id.*?(\d+)',
        r'.*del.*task.*id.*?(\d+)',
    ]
    
    for pattern in delete_patterns:
        delete_match = re.search(pattern, lower_msg)
        if delete_match:
            task_num = int(delete_match.group(1))
            tasks = (await session.exec(
                select(Task).where(Task.user_id == user_id).order_by(Task.created_at.asc())
            )).all()
            
            if 0 < task_num <= len(tasks):
                task = tasks[task_num - 1]
                await session.delete(task)
                await session.commit()
                return {"response": f"✓ Deleted task #{task_num} '{task.title}'"}
            else:
                return {"response": f"Task #{task_num} not found. You have {len(tasks)} task(s)."}
    
    # Greeting
    if lower_msg.startswith(('hello', 'hi', 'hey')):
        return {"response": "Hello! I'm your AI assistant. Tell me to 'add a task to buy groceries' or 'show my tasks'!"}
    
    # Default response
    return {
        "response": f"I understand: '{message}'. Try saying: 'Add a task to buy groceries' or 'Show my tasks'"
    }


@router.post("/chat/conversation", response_model=AIResponse)
async def chat_conversation(
    request: AIRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Chat with the AI assistant.

    This endpoint allows authenticated users to chat with the AI assistant
    for help managing their tasks.
    """
    try:
        # Validate input
        if not request.message or len(request.message.strip()) == 0:
            raise HTTPException(status_code=400, detail="Message is required")

        # Extract user_id from current_user dict
        print(f"DEBUG: current_user = {current_user}")
        print(f"DEBUG: current_user keys = {current_user.keys()}")
        print(f"DEBUG: current_user.get('user_id') = {current_user.get('user_id')}")
        print(f"DEBUG: request.user_id = {request.user_id}")
        
        # Always use user_id from current_user (JWT token), ignore request.user_id
        user_id = current_user.get("user_id") or current_user.get("sub")
        
        print(f"DEBUG: Using user_id: {user_id}")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token")

        # Get AI response (now with actual task management)
        result = await get_ai_response(request.message, user_id, session)
        print(f"DEBUG: AI response result: {result}")

        # Format and return the response
        response = AIResponse(
            response=result.get("response", ""),
            user_id=user_id,
            message=request.message,
            task_created=result.get("task_created", False),
            task_id=result.get("task_id")
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Chat conversation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health")
async def ai_health():
    """
    Health check for the AI assistant service.
    """
    return {"status": "AI assistant service is healthy"}
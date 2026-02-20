"""Task CRUD routes for managing user tasks."""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import or_
from models import Task
from db import get_session
from middleware.jwt_auth import get_current_user_id
from pydantic import BaseModel, constr, validator
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


# Pydantic models for validation
class TaskCreate(BaseModel):
    title: constr(min_length=1, max_length=200)
    description: Optional[constr(max_length=1000)] = None


class TaskUpdate(BaseModel):
    title: Optional[constr(min_length=1, max_length=200)] = None
    description: Optional[constr(max_length=1000)] = None


class TaskResponse(BaseModel):
    id: int
    user_id: str
    title: str
    description: Optional[str] = None
    completed: bool
    created_at: str
    updated_at: str


def validate_task_ownership(task: Task, user_id: str):
    """Validate that task belongs to the authenticated user."""
    if task.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Task does not belong to this user"
        )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id)
):
    """Create a new task for the authenticated user."""
    new_task = Task(
        user_id=user_id,
        title=task_data.title,
        description=task_data.description,
        completed=False
    )

    session.add(new_task)
    await session.commit()
    await session.refresh(new_task)

    return TaskResponse(
        id=new_task.id,
        user_id=new_task.user_id,
        title=new_task.title,
        description=new_task.description,
        completed=new_task.completed,
        created_at=new_task.created_at.isoformat(),
        updated_at=new_task.updated_at.isoformat()
    )


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id)
):
    """Get all tasks for the authenticated user."""
    tasks = (await session.exec(
        select(Task)
        .where(Task.user_id == user_id)
        .order_by(Task.created_at.desc())
    )).all()

    return [
        TaskResponse(
            id=task.id,
            user_id=task.user_id,
            title=task.title,
            description=task.description,
            completed=task.completed,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat()
        )
        for task in tasks
    ]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id)
):
    """Get a specific task by ID."""
    task = await session.get(Task, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    validate_task_ownership(task, user_id)

    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        completed=task.completed,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat()
    )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id)
):
    """Update an existing task."""
    task = await session.get(Task, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    validate_task_ownership(task, user_id)

    # Update only provided fields
    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description

    task.updated_at = datetime.utcnow()

    session.add(task)
    await session.commit()
    await session.refresh(task)

    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        completed=task.completed,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat()
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id)
):
    """Delete a task."""
    task = await session.get(Task, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    validate_task_ownership(task, user_id)

    session.delete(task)
    await session.commit()


@router.patch("/{task_id}/complete", response_model=TaskResponse)
async def toggle_complete(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id)
):
    """Toggle task completion status."""
    task = await session.get(Task, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    validate_task_ownership(task, user_id)

    # Toggle completion status
    task.completed = not task.completed
    task.updated_at = datetime.utcnow()

    session.add(task)
    await session.commit()
    await session.refresh(task)

    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        completed=task.completed,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat()
    )

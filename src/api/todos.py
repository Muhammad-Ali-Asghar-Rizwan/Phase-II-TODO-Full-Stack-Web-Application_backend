from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from ..core.db import get_session
from ..models.todo import Todo
from ..services.todo_service import TodoService
from .auth import get_current_user_token
from typing import Annotated, List

router = APIRouter(prefix="/todos", tags=["todos"])
todo_service = TodoService()

@router.post("/", response_model=Todo)
def create_todo(
    todo: Todo,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user_token)]
):
    todo.owner_id = user["sub"]
    return todo_service.create_todo(session, todo)

@router.get("/", response_model=List[Todo])
def read_todos(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user_token)]
):
    return todo_service.get_todos(session, user["sub"])

@router.put("/{todo_id}", response_model=Todo)
def update_todo(
    todo_id: int,
    todo_update: Todo,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user_token)]
):
    db_todo = todo_service.get_todo(session, todo_id)
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if db_todo.owner_id != user["sub"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    todo_data = todo_update.model_dump(exclude_unset=True)
    for key, value in todo_data.items():
        if key != "id" and key != "owner_id":
            setattr(db_todo, key, value)
            
    return todo_service.update_todo(session, db_todo)

@router.delete("/{todo_id}")
def delete_todo(
    todo_id: int,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[dict, Depends(get_current_user_token)]
):
    db_todo = todo_service.get_todo(session, todo_id)
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if db_todo.owner_id != user["sub"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    todo_service.delete_todo(session, db_todo)
    return {"ok": True}

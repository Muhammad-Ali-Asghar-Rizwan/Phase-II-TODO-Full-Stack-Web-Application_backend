"""
MCP Tools for Task Operations
Implements the tools that the AI agent will use to manipulate tasks
"""

from typing import Dict, Any, List
from sqlmodel import Session
from pydantic import BaseModel
from ..models.todo import Todo
from ..services.todo_service import TodoService


class TaskMCPTask(BaseModel):
    title: str
    description: str = None
    owner_id: str


class TaskMCPUpdate(BaseModel):
    id: int
    title: str = None
    description: str = None
    is_completed: bool = None
    owner_id: str = None


class TaskTools:
    """Collection of MCP tools for task operations"""
    
    def __init__(self, db_session: Session):
        self.session = db_session
        self.service = TodoService()
    
    def create_task(self, title: str, description: str = None, owner_id: str = None) -> Dict[str, Any]:
        """Create a new task"""
        try:
            # Create a new Todo instance
            new_todo = Todo(
                title=title,
                description=description,
                owner_id=owner_id,
                is_completed=False  # Default to not completed
            )
            
            # Use the existing service to create the task
            created_todo = self.service.create_todo(self.session, new_todo)
            
            return {
                "success": True,
                "task_id": created_todo.id,
                "message": f"Task '{created_todo.title}' created successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_tasks(self, owner_id: str, status: str = None) -> Dict[str, Any]:
        """Retrieve tasks for a specific user"""
        try:
            # Get tasks using the existing service
            todos = self.service.get_todos(self.session, owner_id)
            
            # Filter by status if provided
            if status:
                if status.lower() == "completed":
                    todos = [t for t in todos if t.is_completed]
                elif status.lower() == "pending":
                    todos = [t for t in todos if not t.is_completed]
            
            # Format the response
            tasks = []
            for todo in todos:
                tasks.append({
                    "id": todo.id,
                    "title": todo.title,
                    "description": todo.description,
                    "is_completed": todo.is_completed,
                    "created_at": todo.created_at.isoformat(),
                    "updated_at": todo.updated_at.isoformat()
                })
            
            return {
                "success": True,
                "tasks": tasks,
                "count": len(tasks)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_task(self, id: int, title: str = None, description: str = None, is_completed: bool = None, owner_id: str = None) -> Dict[str, Any]:
        """Update an existing task"""
        try:
            # Get the existing task
            existing_todo = self.service.get_todo(self.session, id)
            if not existing_todo:
                return {
                    "success": False,
                    "error": f"Task with id {id} not found"
                }
            
            # Update the fields that were provided
            if title is not None:
                existing_todo.title = title
            if description is not None:
                existing_todo.description = description
            if is_completed is not None:
                existing_todo.is_completed = is_completed
            if owner_id is not None:
                existing_todo.owner_id = owner_id
            
            # Use the existing service to update the task
            updated_todo = self.service.update_todo(self.session, existing_todo)
            
            return {
                "success": True,
                "task_id": updated_todo.id,
                "message": f"Task '{updated_todo.title}' updated successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_task_with_confirmation(self, id: int, confirmed: bool = False) -> Dict[str, Any]:
        """Delete a task with confirmation"""
        try:
            # Get the task to be deleted
            todo_to_delete = self.service.get_todo(self.session, id)
            if not todo_to_delete:
                return {
                    "success": False,
                    "error": f"Task with id {id} not found"
                }
            
            # If not confirmed, return a confirmation request
            if not confirmed:
                return {
                    "success": False,
                    "requires_confirmation": True,
                    "message": f"Are you sure you want to delete the task '{todo_to_delete.title}'?",
                    "task_id": id
                }
            
            # Use the existing service to delete the task
            self.service.delete_todo(self.session, todo_to_delete)
            
            return {
                "success": True,
                "message": f"Task '{todo_to_delete.title}' deleted successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_task(self, id: int) -> Dict[str, Any]:
        """Delete a task (wrapper for backward compatibility)"""
        return self.delete_task_with_confirmation(id, confirmed=True)
    
    def complete_task(self, id: int) -> Dict[str, Any]:
        """Mark a task as completed"""
        try:
            # Get the existing task
            existing_todo = self.service.get_todo(self.session, id)
            if not existing_todo:
                return {
                    "success": False,
                    "error": f"Task with id {id} not found"
                }
            
            # Update the task to mark as completed
            existing_todo.is_completed = True
            updated_todo = self.service.update_todo(self.session, existing_todo)
            
            return {
                "success": True,
                "task_id": updated_todo.id,
                "message": f"Task '{updated_todo.title}' marked as completed"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
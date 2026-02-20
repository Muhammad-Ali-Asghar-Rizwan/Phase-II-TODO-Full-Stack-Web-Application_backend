from sqlmodel import Session, select
from ..models.todo import Todo

class TodoService:
    def create_todo(self, session: Session, todo: Todo) -> Todo:
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo

    def get_todos(self, session: Session, owner_id: str) -> list[Todo]:
        statement = select(Todo).where(Todo.owner_id == owner_id)
        return session.exec(statement).all()

    def get_todo(self, session: Session, todo_id: int) -> Todo | None:
        return session.get(Todo, todo_id)

    def update_todo(self, session: Session, todo: Todo) -> Todo:
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo

    def delete_todo(self, session: Session, todo: Todo):
        session.delete(todo)
        session.commit()

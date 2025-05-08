from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

# Base class for SQLAlchemy models
class ModelBase(SQLModel):
    """Base class for all models."""
    pass

class User(SQLModel, table=True):
    """User model for authentication and group management."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password: str
    role: str
    manager_password: str
    tasks: List["Task"] = Relationship(back_populates="owner")

class Task(SQLModel, table=True):
    """Task model for todo items."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    date: str
    notes: str
    status: str
    assigned_to: str
    remaining_time: str = ""
    time_color: str = "default"
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    owner: Optional[User] = Relationship(back_populates="tasks")
"""Database models for Task Management API."""
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import BaseModel


def get_current_time():
    """Get current UTC time with timezone awareness."""
    return datetime.now(timezone.utc)


class Task(SQLModel, table=True):
    """Task model for database storage."""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: str = Field(default="pending")  # pending, in_progress, completed
    created_at: datetime = Field(default_factory=get_current_time)
    updated_at: datetime = Field(default_factory=get_current_time)


class TaskCreate(BaseModel):
    """Request model for creating a task."""

    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)


class TaskUpdate(BaseModel):
    """Request model for updating a task."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[str] = None


class TaskResponse(BaseModel):
    """Response model for task endpoints."""

    id: int
    title: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

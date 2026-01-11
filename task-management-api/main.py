"""Task Management API - FastAPI application."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Session, select
from database import engine, get_session
from models import Task, TaskCreate, TaskUpdate, TaskResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup: Create database tables
    SQLModel.metadata.create_all(engine)
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Task Management API",
    description="A production-ready Task Management API built with FastAPI and SQLModel",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def get_root():
    """Root endpoint - API health check."""
    return {
        "message": "Task Management API",
        "version": "1.0.0",
        "status": "operational",
    }


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate, session: Annotated[Session, Depends(get_session)]
):
    """Create a new task."""
    task = Task(title=task_data.title, description=task_data.description)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(
    status_filter: str | None = None,
    session: Annotated[Session, Depends(get_session)] = None,
):
    """List all tasks with optional status filtering."""
    statement = select(Task)

    if status_filter:
        # Validate status filter
        valid_statuses = ["pending", "in_progress", "completed"]
        if status_filter not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter. Must be one of: {', '.join(valid_statuses)}",
            )
        statement = statement.where(Task.status == status_filter)

    tasks = session.exec(statement).all()
    return tasks


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int, session: Annotated[Session, Depends(get_session)]
):
    """Get a single task by ID."""
    task = session.get(Task, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )

    return task


@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    session: Annotated[Session, Depends(get_session)],
):
    """Update a task by ID."""
    task = session.get(Task, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )

    # Update only provided fields
    update_data = task_update.model_dump(exclude_unset=True)

    # Validate status if provided
    if "status" in update_data:
        valid_statuses = ["pending", "in_progress", "completed"]
        if update_data["status"] not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )

    # Update fields
    for key, value in update_data.items():
        setattr(task, key, value)

    # Update timestamp
    task.updated_at = datetime.now(timezone.utc)

    session.add(task)
    session.commit()
    session.refresh(task)

    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int, session: Annotated[Session, Depends(get_session)]
):
    """Delete a task by ID."""
    task = session.get(Task, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )

    session.delete(task)
    session.commit()

    return None

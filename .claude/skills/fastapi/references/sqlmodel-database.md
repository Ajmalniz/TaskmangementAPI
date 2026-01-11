# SQLModel + Neon PostgreSQL Reference

Complete guide to adding persistent storage to FastAPI using SQLModel and Neon PostgreSQL. This is the "fast track" approach for getting a database up and running quickly.

## Table of Contents
- Why SQLModel + Neon
- Setting Up Neon
- Installing SQLModel
- Defining Your Model
- Connecting to the Database
- Database Connection Pool with Lifespan
- Creating Tables on Startup
- CRUD Operations with Session
- Complete Example
- Hands-On Exercise
- Common Mistakes
- What About Migrations?

## Why SQLModel + Neon

**The Problem: In-Memory Data Doesn't Persist**

```python
# ❌ Data lost when server restarts!
tasks = []

@app.post("/tasks")
def create_task(task: dict):
    tasks.append(task)  # Lost on restart!
    return task
```

Every time you restart your server, all data disappears. For production APIs, you need persistent storage.

**The Solution: SQLModel + Neon PostgreSQL**

**SQLModel = Pydantic + SQLAlchemy**

- **Pydantic** - Data validation and serialization (you already know this!)
- **SQLAlchemy** - Database ORM (Object-Relational Mapping)
- **SQLModel** - Combines both in one elegant class

You write one model class that works as both:
- Pydantic model for API validation
- SQLAlchemy model for database operations

**Neon = PostgreSQL as a Service**

- Fully managed PostgreSQL database
- No installation or server management
- Free tier for learning and development
- Connection string ready in 30 seconds
- Serverless architecture (auto-scales, auto-pauses)

**This is the "fast track":**
- Get a database running in minutes
- No Docker, no local PostgreSQL installation
- Focus on learning FastAPI patterns
- Production-ready migrations come later (Alembic)

## Setting Up Neon

**Step 1: Create a Neon account**

Visit https://neon.tech and sign up for free.

**Step 2: Create a project**

1. Click "New Project"
2. Choose a name (e.g., "fastapi-learning")
3. Select a region close to you
4. Click "Create Project"

**Step 3: Copy connection string**

After project creation, you'll see a connection string like:

```
postgresql://user:password@ep-cool-term-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**IMPORTANT:** Note the `?sslmode=require` at the end—this is required for Neon!

**Step 4: Add to `.env`**

```bash
# .env
DATABASE_URL=postgresql://user:password@ep-cool-term-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**Step 5: Add to `.gitignore`**

```bash
# .gitignore
.env
```

Never commit your connection string to version control!

**Step 6: Create `.env.example`**

```bash
# .env.example
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

## Installing SQLModel

Always use `uv` to install dependencies:

```bash
# Install SQLModel and PostgreSQL driver
uv add sqlmodel psycopg2-binary
```

**What gets installed:**

- `sqlmodel` - The SQLModel library
- `psycopg2-binary` - PostgreSQL database driver (required for connecting)

**Why both?**

- SQLModel talks to databases through drivers
- psycopg2 is the PostgreSQL driver
- Without it, you'll get: `No module named 'psycopg2'`

## Defining Your Model

A SQLModel is a Pydantic model that's also a database table:

**Basic model:**

```python
from sqlmodel import SQLModel, Field
from typing import Optional

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    status: str = Field(default="pending")
```

**Key points:**

1. **`SQLModel` base class** - Inherits from both Pydantic's BaseModel and SQLAlchemy's Base
2. **`table=True`** - Makes this a database table (without it, it's just a Pydantic model)
3. **`id` field** - Optional[int] with `primary_key=True` (database assigns the ID)
4. **`Field(default=...)`** - SQLModel's Field, works like Pydantic's Field
5. **Type hints** - Define both Python types and database column types

**Field types mapping:**

| Python Type | Database Column |
|-------------|----------------|
| `str` | VARCHAR |
| `int` | INTEGER |
| `float` | FLOAT |
| `bool` | BOOLEAN |
| `Optional[str]` | VARCHAR (nullable) |
| `str = Field(default="...")` | VARCHAR with default |

**Why `Optional[int]` for ID?**

```python
# Creating a new task - no ID yet
task = Task(title="Learn SQLModel", status="pending")
# task.id is None

# After saving to database, ID is assigned
session.add(task)
session.commit()
session.refresh(task)
# task.id is 1 (database assigned it)
```

The ID is `None` before saving, then gets a value from the database.

**Complete model example:**

```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: str = Field(default="pending")
    priority: int = Field(default=1, ge=1, le=5)  # 1-5
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                "title": "Learn SQLModel",
                "description": "Read the docs and build a CRUD API",
                "status": "pending",
                "priority": 2
            }
        }
```

## Connecting to the Database

**Create the engine (database connection):**

```python
from sqlmodel import create_engine
from config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, echo=True)
```

**Parameters:**

- `settings.database_url` - PostgreSQL connection string from .env
- `echo=True` - Logs all SQL queries (helpful for learning, disable in production)

**Where to create the engine?**

Create it once at the module level, not inside functions:

```python
# database.py
from sqlmodel import create_engine, Session
from config import get_settings

settings = get_settings()

# Create engine once at module level
engine = create_engine(settings.database_url, echo=True)

# Dependency for getting a session
def get_session():
    with Session(engine) as session:
        yield session
```

**Why at module level?**

- Engine is expensive to create
- Should be created once and reused
- Don't create a new engine for every request!

## Database Connection Pool with Lifespan

For production applications, use the **lifespan pattern** to manage database connection pools with proper startup and shutdown:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import create_engine, Session, SQLModel
from config import get_settings

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Create database connection pool
    print("Creating database connection pool...")
    app.state.engine = create_engine(
        settings.database_url,
        echo=True,
        pool_size=10,          # Maximum connections in pool
        max_overflow=20,       # Extra connections if needed
        pool_timeout=30,       # Seconds to wait for connection
        pool_pre_ping=True     # Test connections before using
    )

    # Create tables
    SQLModel.metadata.create_all(app.state.engine)
    print("Database ready!")

    yield  # Application runs

    # SHUTDOWN: Clean up connection pool
    print("Closing database connection pool...")
    app.state.engine.dispose()
    print("Database shutdown complete")

app = FastAPI(lifespan=lifespan)

# Access engine from app.state
def get_session():
    with Session(app.state.engine) as session:
        yield session
```

**Why use lifespan for database?**

1. **Proper connection pool management** - Pool created once at startup, disposed at shutdown
2. **Graceful shutdown** - Ensures all connections are closed cleanly
3. **Configuration** - Set pool size, timeouts, and health checks
4. **Logging** - Track when pool is created and destroyed
5. **Modern pattern** - Replaces deprecated `@app.on_event()` pattern

**Connection pool parameters:**

- `pool_size=10` - Keep 10 connections ready
- `max_overflow=20` - Create up to 20 extra connections if needed
- `pool_timeout=30` - Wait 30 seconds for available connection
- `pool_pre_ping=True` - Test connections before using (prevents stale connections)

**Module-level vs Lifespan:**

```python
# ✅ SIMPLE: Module-level (good for learning/development)
engine = create_engine(settings.database_url, echo=True)

# ✅ PRODUCTION: Lifespan with connection pool
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = create_engine(
        settings.database_url,
        pool_size=10,
        pool_pre_ping=True
    )
    yield
    app.state.engine.dispose()
```

**See [references/lifespan-events.md](lifespan-events.md) for:**
- Complete lifespan pattern guide
- Multiple resource initialization
- Preloading ML models
- External client setup
- Production-ready examples

## Creating Tables on Startup

FastAPI has lifecycle events for running code at startup:

```python
from fastapi import FastAPI
from sqlmodel import SQLModel
from database import engine

app = FastAPI()

@app.on_event("startup")
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
```

**What this does:**

1. On startup, FastAPI calls `create_db_and_tables()`
2. `SQLModel.metadata.create_all(engine)` creates tables for all models with `table=True`
3. If tables already exist, it does nothing (safe to run multiple times)

**Complete startup example:**

```python
from fastapi import FastAPI
from sqlmodel import SQLModel
from database import engine
import models  # Import so SQLModel knows about your models

app = FastAPI()

@app.on_event("startup")
def create_db_and_tables():
    """Create database tables on startup."""
    print("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    print("Database tables created!")
```

**Important:** Import your models before calling `create_all()`:

```python
# ✅ CORRECT - Import models first
import models
SQLModel.metadata.create_all(engine)

# ❌ WRONG - SQLModel doesn't know about models
SQLModel.metadata.create_all(engine)
import models  # Too late!
```

## CRUD Operations with Session

The `Session` is your interface to the database. Use dependency injection to get a session in your endpoints:

```python
from fastapi import Depends
from sqlmodel import Session
from database import get_session

@app.post("/tasks")
def create_task(task: Task, session: Session = Depends(get_session)):
    # Use session to interact with database
    pass
```

### Create

Add a new record to the database:

```python
from fastapi import Depends
from sqlmodel import Session
from database import get_session
from models import Task

@app.post("/tasks", response_model=Task)
def create_task(task: Task, session: Session = Depends(get_session)):
    session.add(task)           # Stage the task
    session.commit()             # Save to database
    session.refresh(task)        # Get the assigned ID
    return task
```

**Three steps:**

1. **`session.add(task)`** - Stage the task for saving (not saved yet!)
2. **`session.commit()`** - Execute the SQL INSERT, save to database
3. **`session.refresh(task)`** - Reload from database to get assigned ID and defaults

**Why `refresh()`?**

```python
task = Task(title="Learn FastAPI")
print(task.id)  # None

session.add(task)
session.commit()
print(task.id)  # Still None! Not updated yet

session.refresh(task)
print(task.id)  # 1 - Now has the database-assigned ID!
```

### Read List

Get all records with optional filtering:

```python
from sqlmodel import select

@app.get("/tasks", response_model=list[Task])
def list_tasks(
    status: str | None = None,
    session: Session = Depends(get_session)
):
    statement = select(Task)

    if status:
        statement = statement.where(Task.status == status)

    tasks = session.exec(statement).all()
    return tasks
```

**Key concepts:**

- `select(Task)` - Creates a SELECT query
- `.where(Task.status == status)` - Adds a WHERE clause (optional filtering)
- `session.exec(statement)` - Executes the query
- `.all()` - Returns all results as a list

**SQL generated:**

```sql
-- Without filter
SELECT * FROM task;

-- With filter
SELECT * FROM task WHERE status = 'pending';
```

### Read Single

Get one record by ID:

```python
from fastapi import HTTPException

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task
```

**`session.get(Model, id)` - Shortcut for getting by primary key**

Equivalent to:

```python
statement = select(Task).where(Task.id == task_id)
task = session.exec(statement).first()
```

### Update

Modify an existing record:

```python
@app.put("/tasks/{task_id}", response_model=Task)
def update_task(
    task_id: int,
    task_update: Task,
    session: Session = Depends(get_session)
):
    # Get existing task
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update fields
    task.title = task_update.title
    task.description = task_update.description
    task.status = task_update.status

    # Save changes
    session.add(task)
    session.commit()
    session.refresh(task)

    return task
```

**Steps:**

1. **Get the existing record** - `session.get(Task, task_id)`
2. **Modify the fields** - `task.title = ...`
3. **Save changes** - `session.add()`, `session.commit()`, `session.refresh()`

**Better update pattern with Pydantic:**

```python
from pydantic import BaseModel

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None

@app.patch("/tasks/{task_id}", response_model=Task)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    session: Session = Depends(get_session)
):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update only provided fields
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    session.add(task)
    session.commit()
    session.refresh(task)

    return task
```

**Why separate `TaskUpdate` model?**

- Allows partial updates (PATCH semantics)
- Only provided fields are updated
- `model_dump(exclude_unset=True)` ignores fields not sent

### Delete

Remove a record:

```python
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    session.delete(task)
    session.commit()

    return {"message": "Task deleted", "task_id": task_id}
```

**Steps:**

1. **Get the record** - `session.get(Task, task_id)`
2. **Delete it** - `session.delete(task)`
3. **Commit** - `session.commit()`

**No `refresh()` needed - the record is gone!**

## Complete Example

A full Task API with SQLModel and Neon:

**Project structure:**

```
my-task-api/
├── .env                  # DATABASE_URL (not committed)
├── .env.example          # Template
├── .gitignore            # Contains .env
├── pyproject.toml        # uv dependencies
├── config.py             # Settings
├── models.py             # Task model
├── database.py           # Engine and session
└── main.py               # FastAPI app
```

**config.py:**

```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**models.py:**

```python
from sqlmodel import SQLModel, Field
from typing import Optional

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: str = Field(default="pending")
```

**database.py:**

```python
from sqlmodel import create_engine, Session
from config import get_settings

settings = get_settings()

# Create engine with echo for debugging
engine = create_engine(settings.database_url, echo=True)

# Dependency for getting a session
def get_session():
    with Session(engine) as session:
        yield session
```

**main.py:**

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Session, select
from database import engine, get_session
from models import Task

app = FastAPI()

@app.on_event("startup")
def create_db_and_tables():
    """Create database tables on startup."""
    SQLModel.metadata.create_all(engine)

# CREATE
@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task: Task, session: Session = Depends(get_session)):
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

# READ LIST
@app.get("/tasks", response_model=list[Task])
def list_tasks(
    status: str | None = None,
    session: Session = Depends(get_session)
):
    statement = select(Task)
    if status:
        statement = statement.where(Task.status == status)
    tasks = session.exec(statement).all()
    return tasks

# READ SINGLE
@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# UPDATE
@app.put("/tasks/{task_id}", response_model=Task)
def update_task(
    task_id: int,
    task_update: Task,
    session: Session = Depends(get_session)
):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.title = task_update.title
    task.description = task_update.description
    task.status = task_update.status

    session.add(task)
    session.commit()
    session.refresh(task)
    return task

# DELETE
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    session.delete(task)
    session.commit()
    return {"message": "Task deleted", "task_id": task_id}
```

**.env:**

```bash
DATABASE_URL=postgresql://user:password@ep-cool-term-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**.env.example:**

```bash
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

## Hands-On Exercise

Build a complete Task API with SQLModel and Neon:

**Step 1: Set up Neon**

1. Go to https://neon.tech and create a free account
2. Create a new project named "fastapi-tasks"
3. Copy the connection string (includes `?sslmode=require`)

**Step 2: Initialize project**

```bash
uv init task-api
cd task-api
uv add "fastapi[standard]" sqlmodel psycopg2-binary pydantic-settings
```

**Step 3: Create `.env`**

```bash
# .env
DATABASE_URL=postgresql://your-connection-string-here?sslmode=require
```

**Step 4: Add to `.gitignore`**

```bash
echo ".env" >> .gitignore
```

**Step 5: Create `config.py`**

```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Step 6: Create `models.py`**

```python
from sqlmodel import SQLModel, Field
from typing import Optional

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    status: str = Field(default="pending")
```

**Step 7: Create `database.py`**

```python
from sqlmodel import create_engine, Session
from config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, echo=True)

def get_session():
    with Session(engine) as session:
        yield session
```

**Step 8: Create `main.py`**

```python
from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, Session, select
from database import engine, get_session
from models import Task

app = FastAPI()

@app.on_event("startup")
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@app.post("/tasks", response_model=Task)
def create_task(task: Task, session: Session = Depends(get_session)):
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@app.get("/tasks", response_model=list[Task])
def list_tasks(session: Session = Depends(get_session)):
    tasks = session.exec(select(Task)).all()
    return tasks
```

**Step 9: Run the app**

```bash
uv run uvicorn main:app --reload
```

**Step 10: Test with curl**

```bash
# Create a task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn SQLModel", "status": "pending"}'

# List tasks
curl http://localhost:8000/tasks
```

**Step 11: Verify in Neon dashboard**

1. Go to your Neon project dashboard
2. Click "SQL Editor"
3. Run: `SELECT * FROM task;`
4. See your data persisted in PostgreSQL!

**Step 12: Restart and verify persistence**

```bash
# Stop the server (Ctrl+C)
# Start it again
uv run uvicorn main:app --reload

# Data is still there!
curl http://localhost:8000/tasks
```

## Common Mistakes

**Mistake 1: Forgetting `table=True`**

```python
# ❌ WRONG - Not a table, just a Pydantic model!
class Task(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str

# ✅ CORRECT - table=True makes it a database table
class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
```

**Mistake 2: Missing primary key**

```python
# ❌ WRONG - No primary key!
class Task(SQLModel, table=True):
    title: str
    status: str

# Error: Table 'task' must have at least one primary key column

# ✅ CORRECT - Always have a primary key
class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    status: str
```

**Mistake 3: Not calling `commit()`**

```python
# ❌ WRONG - Changes not saved!
@app.post("/tasks")
def create_task(task: Task, session: Session = Depends(get_session)):
    session.add(task)
    # Forgot session.commit()!
    return task

# ✅ CORRECT - Always commit to save changes
@app.post("/tasks")
def create_task(task: Task, session: Session = Depends(get_session)):
    session.add(task)
    session.commit()
    session.refresh(task)
    return task
```

**Mistake 4: Wrong connection string format**

```bash
# ❌ WRONG - Missing ?sslmode=require for Neon
DATABASE_URL=postgresql://user:pass@ep-xxx.aws.neon.tech/neondb

# ✅ CORRECT - Neon requires sslmode=require
DATABASE_URL=postgresql://user:pass@ep-xxx.aws.neon.tech/neondb?sslmode=require
```

**Mistake 5: Not importing models before `create_all()`**

```python
# ❌ WRONG - SQLModel doesn't know about Task model
from sqlmodel import SQLModel
from database import engine

SQLModel.metadata.create_all(engine)
import models  # Too late!

# ✅ CORRECT - Import models first
from sqlmodel import SQLModel
from database import engine
import models  # Import so SQLModel knows about models

SQLModel.metadata.create_all(engine)
```

**Mistake 6: Creating engine per request**

```python
# ❌ WRONG - Creates new engine for every request!
def get_session():
    engine = create_engine(settings.database_url)  # Expensive!
    with Session(engine) as session:
        yield session

# ✅ CORRECT - Create engine once at module level
engine = create_engine(settings.database_url)

def get_session():
    with Session(engine) as session:
        yield session
```

**Mistake 7: Forgetting to refresh after commit**

```python
# ❌ WRONG - task.id is still None!
@app.post("/tasks")
def create_task(task: Task, session: Session = Depends(get_session)):
    session.add(task)
    session.commit()
    return task  # task.id is None, not the assigned ID!

# ✅ CORRECT - Refresh to get assigned ID
@app.post("/tasks")
def create_task(task: Task, session: Session = Depends(get_session)):
    session.add(task)
    session.commit()
    session.refresh(task)  # Now task.id has the database-assigned value
    return task
```

## What About Migrations?

This guide uses `SQLModel.metadata.create_all()` to create tables. This is the "fast track" for learning and development.

**What `create_all()` does:**

- Creates tables if they don't exist
- Safe to run multiple times
- **Does NOT update existing tables** - if you change your model, it won't alter the table

**The Problem:**

```python
# Original model
class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str

# You change it to add status
class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    status: str = Field(default="pending")  # NEW FIELD

# create_all() does NOTHING - table already exists!
SQLModel.metadata.create_all(engine)
```

**Solutions:**

1. **For learning/development** - Delete the table and recreate:
   ```sql
   DROP TABLE task;
   ```
   Then restart your app to recreate.

2. **For production** - Use Alembic for migrations (covered in advanced topics):
   ```bash
   alembic revision --autogenerate -m "Add status column"
   alembic upgrade head
   ```

**When to use each:**

| Approach | Use Case |
|----------|----------|
| `create_all()` | Learning, prototypes, hackathons |
| Alembic | Production, teams, schema changes |

**This guide focuses on the fast track** - `create_all()` gets you productive immediately. When you're ready for production, learn Alembic for managing schema migrations.

## User Management

SQLModel is perfect for user management with password hashing:

**User model example:**

```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import EmailStr

class User(SQLModel, table=True):
    """Database model for users."""
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str  # Note: hashed, not plaintext
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(SQLModel):
    """Request model for signup."""
    email: EmailStr
    password: str = Field(min_length=8)

class UserResponse(SQLModel):
    """Response model (excludes password hash)."""
    id: int
    email: EmailStr
    created_at: datetime
```

**Key features:**

- `email` is `unique=True` and `index=True` for fast lookups
- `hashed_password` field name makes it clear this is NOT plaintext
- `EmailStr` validates email format automatically
- Separate models for request (UserCreate), database (User), and response (UserResponse)

**See [references/user-management.md](user-management.md) for:**
- Complete password hashing guide with Argon2
- User signup endpoint implementation
- Security principles for password storage
- How to never store plaintext passwords
- Common security mistakes to avoid

## Key Points

- SQLModel combines Pydantic validation with SQLAlchemy ORM
- Neon provides managed PostgreSQL with no setup required
- Install with: `uv add sqlmodel psycopg2-binary`
- Models need `table=True` and a primary key field
- Connection string for Neon must include `?sslmode=require`
- Create engine once at module level, not per request
- Use `get_session()` dependency with `yield` for session management
- CRUD operations: `add()` + `commit()` + `refresh()` for create, `select()` for read, modify + `commit()` for update, `delete()` + `commit()` for delete
- Create tables on startup with `@app.on_event("startup")` and `create_all()`
- This is the "fast track" - production apps use Alembic for migrations
- Always add `.env` to `.gitignore` and create `.env.example`

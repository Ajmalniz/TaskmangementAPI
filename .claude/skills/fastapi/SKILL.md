---
name: fastapi
description: Comprehensive FastAPI development skill for building Python web APIs. CRITICAL - ALWAYS use uv package manager (uv init + uv add "fastapi[standard]") to create projects. Generate code with mandatory type hints on all parameters, descriptive function names matching endpoint purpose, and dictionary returns only (never None). Use when building REST APIs, creating web services, implementing backends, or when the user mentions FastAPI.
---

# FastAPI Development Skill

Build FastAPI applications from hello world to production-ready APIs using official documentation patterns.

## ⚠️ MANDATORY WORKFLOW - READ THIS FIRST

**CRITICAL: Every FastAPI project MUST follow this exact sequence. DO NOT skip steps!**

### Step-by-Step Project Creation:

1. **Initialize project with uv:**
   ```bash
   uv init <project-name>
   cd <project-name>
   ```

2. **Install FastAPI with all standard dependencies:**
   ```bash
   uv add "fastapi[standard]"
   ```
   This installs: FastAPI, uvicorn, pydantic, httpx, email-validator, and more.

3. **Create main.py with code that follows ALL principles:**
   - ✅ Type hints on ALL path and query parameters
   - ✅ Return dictionaries, NEVER None
   - ✅ Use descriptive function names (e.g., `get_user`, `search_items`)

4. **Run the application:**
   ```bash
   uv run uvicorn main:app --reload
   # OR
   uv run fastapi dev main.py
   ```

### ❌ NEVER Do This:
- Create `.py` files outside a uv project
- Use system Python or pip
- Skip `uv init` or `uv add "fastapi[standard]"`
- Create functions without type hints
- Return `None` from endpoints
- Use generic names like `handler()`, `endpoint()`, or `root()`

### ✅ Validation Checklist:
Before completing ANY FastAPI task, verify:
- [ ] Project created with `uv init`
- [ ] `pyproject.toml` exists with `fastapi[standard]` dependency
- [ ] `uv.lock` file exists (confirms reproducible builds)
- [ ] `.venv` directory exists (virtual environment)
- [ ] All function parameters have type hints
- [ ] All endpoints return dictionaries (not None)
- [ ] Function names are descriptive and purpose-driven
- [ ] Application runs with `uv run`

### 📝 Complete Example Following All Principles:

```python
from fastapi import FastAPI

app = FastAPI()

# ✅ CORRECT - Type hints, descriptive name, returns dictionary
@app.get("/")
async def get_welcome_message():
    return {"message": "Welcome to my API!", "status": "operational"}

# ✅ CORRECT - Path parameter with type hint
@app.get("/users/{user_id}")
async def get_user_by_id(user_id: int):
    return {"user_id": user_id, "name": f"User {user_id}"}

# ✅ CORRECT - Query parameters with type hints and defaults
@app.get("/search")
async def search_items(
    q: str,                    # Required parameter
    limit: int = 10,           # Optional with default
    category: str | None = None # Nullable parameter
):
    return {
        "query": q,
        "limit": limit,
        "category": category,
        "results": []
    }

# ❌ WRONG - Missing type hints
@app.get("/wrong")
async def handler(id, name=None):  # DON'T DO THIS!
    return None  # DON'T RETURN NONE!
```

---

## Quick Start

### Create New Project with uv

Always use [uv](https://docs.astral.sh/uv/) package manager for FastAPI projects:

```bash
# Initialize a new Python project
uv init my-api
cd my-api

# Create virtual environment and install FastAPI with all standard dependencies
uv add "fastapi[standard]"

# Create main.py
cat > main.py << 'EOF'
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello World"}
EOF

# Run development server
fastapi dev main.py
```

**Why uv?**
- Extremely fast package installation (10-100x faster than pip)
- Built-in virtual environment management
- Reproducible builds with `uv.lock`
- Drop-in replacement for pip, pip-tools, and virtualenv

### Alternative: Use Project Scaffolding Script

For complex projects with custom structure:

```bash
# Basic project
python scripts/create_project.py my-api

# With Docker support
python scripts/create_project.py my-api --with-docker

# With tests
python scripts/create_project.py my-api --with-tests

# Full stack
python scripts/create_project.py my-api --with-docker --with-tests
```

### Hello World

For the simplest FastAPI app, copy from `assets/hello-world/`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

Run with:
```bash
fastapi dev main.py
```

### Production-Ready Template

For a complete production structure, copy from `assets/production-template/`:
- Structured layout (routers, schemas, services)
- Configuration management
- Middleware (CORS, GZip)
- Testing with pytest
- Docker deployment
- Environment variables

## Core Patterns

### Path Operations

Basic HTTP methods and routing:

```python
@app.get("/items/")           # List items
@app.get("/items/{id}")       # Get item
@app.post("/items/")          # Create item
@app.put("/items/{id}")       # Update item
@app.delete("/items/{id}")    # Delete item
```

#### Why CRUD Is the Foundation

CRUD (Create, Read, Update, Delete) is the foundation of data-driven APIs. This matters for agents because every agent that manages state needs CRUD operations:

- **Memory agents** create memories, read relevant ones, update importance scores, delete stale entries
- **Task agents** create tasks, read pending work, update status, delete completed items
- **Session agents** create conversations, read context, update metadata, delete expired sessions

Every one of these is CRUD. Master these four operations, and you can build the data layer for any agent.

#### HTTP Methods and CRUD

Each CRUD operation maps to an HTTP method with specific semantics:

| Operation  | HTTP Method | Endpoint Example | Description           |
| ---------- | ----------- | ---------------- | --------------------- |
| Create     | POST        | POST /tasks      | Create a new task     |
| Read (all) | GET         | GET /tasks       | List all tasks        |
| Read (one) | GET         | GET /tasks/1     | Get task with ID 1    |
| Update     | PUT         | PUT /tasks/1     | Update task with ID 1 |
| Delete     | DELETE      | DELETE /tasks/1  | Delete task with ID 1 |

**Why these specific mappings?** HTTP methods have semantics:

* **GET** is _safe_—it doesn't change server state. Browsers can cache GET responses.
* **POST** creates new resources. Not safe, not idempotent.
* **PUT** replaces a resource. Idempotent—calling it twice has the same effect as once.
* **DELETE** removes a resource. Also idempotent.

These semantics matter for agents. If an agent's HTTP call fails partway through, idempotent operations (PUT, DELETE) can be safely retried. Non-idempotent operations (POST) require more careful handling.

**See [references/path-operations.md](references/path-operations.md) for:**
- Path parameters with type hints
- Query parameters (required, optional, default values)
- Request body with Pydantic models
- Response models
- Data validation
- Multiple parameter types

**See [references/crud-operations.md](references/crud-operations.md) for:**
- Complete CRUD operations guide
- HTTP method semantics (GET is safe, PUT/DELETE are idempotent)
- Filtering list endpoints
- Update patterns (PUT vs PATCH)
- Error handling (404 for not found)
- Complete Task API implementation
- Common mistakes and best practices

### Request/Response Handling

#### Why Pydantic Matters for Agents

When building APIs that agents call, Pydantic validation is critical:

- **Agents can't guess** - They call exactly what your API exposes
- **Errors cascade** - Bad data gets rejected at the door, not halfway through an expensive LLM call
- **Type safety at boundaries** - When agents compose tools, one agent's output becomes another's input. Type safety prevents cascading failures
- **Automatic validation** - FastAPI uses Pydantic to parse raw JSON bytes, validate data types, check required fields, and reject invalid data with helpful error messages

This validation layer is critical when agents compose tools, similar to how MCP servers validate tool parameters (Chapter 37).

#### Request and Response Models

```python
from pydantic import BaseModel

# Request model - what client sends
class TaskCreate(BaseModel):
    title: str
    description: str | None = None

# Response model - what API returns
class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: str

@app.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate):
    new_task = {
        "id": len(tasks) + 1,
        "title": task.title,
        "description": task.description,
        "status": "pending"
    }
    tasks.append(new_task)
    return new_task
```

**Why two models?** The client shouldn't provide `id` or `status`—those are set by the server. Separating models keeps responsibilities clear.

- **Client says:** "Create a task with this title"
- **Server says:** "Here's your task with ID 1, status pending"

FastAPI automatically:
- Validates request data
- Converts types
- Generates API documentation
- Returns proper HTTP responses

### Error Handling

When things go wrong, your API needs to communicate clearly. Good error handling makes APIs predictable—and predictability matters enormously for agents.

#### Why Error Handling Matters for Agents

When agents call your API, they need to programmatically decide what to do:

* **Retry on transient failures** (5xx errors)
* **Report bad input to users** (4xx errors with helpful messages)
* **Handle missing resources gracefully** (404 → create new one? skip?)
* **Never retry on business rule violations** (400 → input fundamentally wrong)

#### Using HTTPException

```python
from fastapi import HTTPException, status

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = find_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    return task
```

**Key points:**
- Use `raise HTTPException`, not `return`
- Use `status` module constants for readability
- Return appropriate status codes (404 for not found, 400 for bad request)

#### 400 vs 422

**422 Unprocessable Entity** — Pydantic validation failed (schema doesn't match)

```python
# Automatic - Pydantic returns 422
POST /tasks
{"description": "Missing title"}  # → 422
```

**400 Bad Request** — Business logic validation failed (schema matches, but violates rules)

```python
# Manual - You check business rules
@app.post("/tasks")
def create_task(task: TaskCreate):
    if not task.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title cannot be empty or whitespace"
        )
```

**See [references/error-handling.md](references/error-handling.md) for:**
- Complete error handling guide
- HTTP status code semantics
- Error message design for agents
- Common mistakes and best practices
- Structured error responses

### Dependency Injection

Every endpoint in your API needs shared resources: configuration, connections, services. You could create these inside each function, but that's repetitive and makes testing hard. Dependency injection solves this—FastAPI creates what your endpoint needs and passes it in.

This pattern powers everything in the rest of this chapter. Settings, database sessions, authentication—all use `Depends()`.

**Basic pattern:**

```python
from fastapi import Depends

def get_config():
    """Provide configuration to endpoints."""
    return {"app_name": "Task API", "version": "1.0"}

@app.get("/tasks")
def list_tasks(config: dict = Depends(get_config)):
    return {"app": config["app_name"]}
```

**Key concepts:**
- Dependencies are just functions (or classes)
- Use `@lru_cache` for expensive, static dependencies
- Use `yield` for dependencies that need cleanup
- FastAPI resolves dependency chains automatically

**See [references/dependencies.md](references/dependencies.md) for:**
- The problem and solution (repeated setup)
- Basic dependencies
- Classes as dependencies
- Caching with lru_cache
- Sub-dependencies
- Dependencies with yield (setup/teardown)
- Global dependencies
- Dependency overrides for testing
- Common mistakes and best practices
- Hands-on exercises

## Environment Configuration

Never hardcode secrets, API keys, or environment-specific settings. Use environment variables with pydantic-settings for type-safe configuration.

**Basic pattern:**

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str
    api_key: str
    debug: bool = False

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Critical security practices:**
- Add `.env` to `.gitignore`
- Create `.env.example` template (committed, no secrets)
- Never commit secrets to version control

**See [references/environment-variables.md](references/environment-variables.md) for:**
- Complete pydantic-settings guide
- .env file setup and security
- Validation and error handling
- Hands-on exercises
- Security checklist

## Database Integration with SQLModel

Connect your FastAPI app to PostgreSQL using SQLModel (Pydantic + SQLAlchemy). This is the "fast track" approach for persistent storage.

**Basic pattern:**

```python
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    status: str = Field(default="pending")

engine = create_engine(settings.database_url)

@app.on_event("startup")
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

@app.post("/tasks")
def create_task(task: Task, session: Session = Depends(get_session)):
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@app.get("/tasks")
def list_tasks(session: Session = Depends(get_session)):
    tasks = session.exec(select(Task)).all()
    return tasks
```

**Key concepts:**
- `table=True` makes it a database table
- `create_engine()` connects to database
- `get_session()` dependency provides Session with yield
- `commit()` saves changes, `refresh()` gets database-assigned ID
- `select()` creates queries, `exec()` executes them

**Install dependencies:**

```bash
uv add sqlmodel psycopg2-binary
```

**See [references/sqlmodel-database.md](references/sqlmodel-database.md) for:**
- Neon PostgreSQL setup (managed database, no installation)
- Complete SQLModel patterns
- CRUD operations with Session
- Table creation on startup
- Model definition with Field types
- Connection string format (`?sslmode=require` for Neon)
- Complete working examples
- Common mistakes and best practices
- Migration strategy (create_all vs Alembic)

## User Management & Password Hashing

Before storing passwords, understand: **you never store passwords**. You store _hashes_.

**Why password hashing matters:**
- If database leaks, attackers get useless hashes (not plaintext passwords)
- Argon2 is the gold standard (memory-hard, GPU-resistant)
- Each hash must be cracked individually—expensive and slow

**Basic pattern:**

```python
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pydantic import EmailStr

password_hash = PasswordHash((Argon2Hasher(),))

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)

class User(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str  # Named explicitly to avoid confusion

class UserCreate(SQLModel):
    email: EmailStr
    password: str = Field(min_length=8)

class UserResponse(SQLModel):
    id: int
    email: EmailStr

@app.post("/users/signup", response_model=UserResponse)
def signup(user: UserCreate, session: Session = Depends(get_session)):
    # Check for duplicate email
    existing = session.exec(select(User).where(User.email == user.email)).first()
    if existing:
        raise HTTPException(400, "Email already registered")

    # Hash password and create user
    hashed = hash_password(user.password)
    db_user = User(email=user.email, hashed_password=hashed)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
```

**Security principles:**
- Never store plaintext passwords
- Never return hashes in API responses
- Use `hashed_password` field name (not `password`)
- Check for duplicate emails before creating users
- Use Argon2 (not MD5/SHA)

**Install dependencies:**

```bash
uv add "pwdlib[argon2]" email-validator
```

**See [references/user-management.md](references/user-management.md) for:**
- Complete password hashing guide
- Why Argon2 is the gold standard
- User signup endpoint implementation
- Security best practices
- Hands-on exercises
- Common mistakes to avoid
- Preview of JWT authentication (next step)

## JWT Authentication

HTTP is stateless—tokens enable authentication without session storage. Users log in once, get a token, and include it in subsequent requests.

**How JWT works:**
1. User sends email/password to `/token`
2. Server verifies password and creates signed JWT
3. User includes token in `Authorization: Bearer <token>` header
4. Server validates signature and extracts user identity

**Basic pattern:**

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime, timedelta

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Token creation
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")

# Login endpoint
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Find user and verify password
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password")

    # Create and return token
    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# Get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    email = payload.get("sub")
    user = session.exec(select(User).where(User.email == email)).first()
    return user

# Protected route
@app.get("/users/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
```

**Key concepts:**
- JWTs are signed (not encrypted) - anyone can read, only server can create valid signatures
- OAuth2 uses form data for `/token` endpoint (not JSON)
- Use `Authorization: Bearer <token>` header for protected routes
- Swagger UI has built-in OAuth2 support (Authorize button)
- Token contains `{"sub": email, "exp": timestamp}` - only identifiers, not sensitive data

**Install dependencies:**

```bash
uv add "python-jose[cryptography]"
```

**Generate secure secret key:**

```bash
openssl rand -hex 32
```

**See [references/jwt-authentication.md](references/jwt-authentication.md) for:**
- Complete JWT implementation guide
- Token creation and validation functions
- Protected route patterns
- OAuth2 password flow
- Protecting task routes with user ownership
- Swagger UI integration
- Complete authentication flow diagram
- Common mistakes and best practices

## Security and Authentication

FastAPI provides built-in security utilities:

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/users/me")
async def read_users_me(token: Annotated[str, Depends(oauth2_scheme)]):
    return decode_token(token)
```

**See [references/security.md](references/security.md) for:**
- OAuth2 with Password and Bearer
- OAuth2 with JWT tokens (production-ready)
- API Key authentication (header, query, cookie)
- HTTP Basic Auth
- Security best practices
- Password hashing
- Role-based access control

## Middleware and CORS

Middleware intercepts every request before endpoints and every response before returning to clients. This solves two critical problems for agent APIs:

1. **CORS** - Frontends on different domains need permission to call your API
2. **Observability** - Track request timing, logging, and headers

**Basic middleware pattern:**

```python
from fastapi import FastAPI, Request
import time

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

**CORS configuration:**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Key concepts:**
- Middleware executes in reverse order (last added = outermost)
- CORS must allow explicit origins when `allow_credentials=True` (not `["*"]`)
- Use `await call_next(request)` to pass to next middleware/route
- Always return the response

**See [references/middleware-cors.md](references/middleware-cors.md) for:**
- Complete middleware guide
- Custom middleware patterns (timing, logging, request ID)
- CORS configuration and parameters
- Production vs development setup
- Request logging and timing
- Middleware execution order (stack behavior)
- Common mistakes and best practices
- Why middleware matters for agent APIs

## Testing with Pytest

### Why Testing Matters for Agent APIs

Testing isn't optional for FastAPI applications, especially when building agent-facing APIs:

- **Agents can't guess** - They call exactly what your API exposes. No documentation mismatch, no hand-waving about "expected" behavior
- **Errors cascade** - A broken endpoint breaks every agent that uses it. One failing endpoint can take down entire workflows
- **Debugging is hard** - Agent failures often trace back to subtle API changes. Tests catch these before agents do
- **Confidence enables iteration** - Tests let you refactor without fear. You can improve your code knowing nothing broke

**Testing isn't something you add later—it's how you verify your code does what you think it does.**

### Install Pytest

Always use `uv` to install pytest as a development dependency:

```bash
uv add --dev pytest
```

Note: `httpx` (required by TestClient) is already included with `fastapi[standard]`.

### The Red-Green Cycle (TDD Fundamentals)

Test-Driven Development (TDD) follows a simple rhythm:

1. **Write a failing test (RED)** - Test something that doesn't exist yet
2. **Make it pass (GREEN)** - Write the minimum code to pass the test
3. **Refactor** - Clean up your code while tests stay green

**Example: Building a `/health` endpoint**

**Step 1: Write the test first (RED)**
```python
# test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """GET /health returns operational status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "operational"}
```

**Run it: `pytest test_main.py -v`**
```
test_main.py::test_health_check FAILED  # ❌ RED - Expected!
```

**Step 2: Make it pass (GREEN)**
```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def get_health_status():
    return {"status": "operational"}
```

**Run again: `pytest test_main.py -v`**
```
test_main.py::test_health_check PASSED  # ✅ GREEN - Success!
```

**Step 3: Refactor (optional)**
```python
# Improve the endpoint with more details
@app.get("/health")
async def get_health_status():
    return {
        "status": "operational",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
```

Tests still pass! You can refactor with confidence.

### Quick Testing Example

Basic test structure for FastAPI:

```python
# test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    """Test root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}

def test_create_item():
    """Test POST creates item with correct data."""
    response = client.post(
        "/items/",
        json={"name": "Test Item", "price": 10.99}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Item"
    assert response.json()["price"] == 10.99

def test_invalid_item():
    """Test validation rejects invalid data."""
    response = client.post(
        "/items/",
        json={"name": ""}  # Empty name should fail
    )
    assert response.status_code == 422  # Validation error
```

### Running Tests

```bash
# Run all tests with verbose output
uv run pytest -v

# Run specific test file
uv run pytest test_main.py -v

# Run tests matching a pattern
uv run pytest -k "test_create" -v

# Run with coverage report
uv run pytest --cov=. --cov-report=html
```

### Test Organization

For larger projects, organize tests in a dedicated directory:

```
my-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── routers/
│       └── items.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Shared fixtures
│   ├── test_main.py
│   └── test_items.py
├── pyproject.toml
└── pytest.ini               # Pytest configuration
```

**Example pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
```

### Common Testing Patterns

**Testing path parameters:**
```python
def test_get_item_by_id():
    response = client.get("/items/123")
    assert response.status_code == 200
    assert response.json()["id"] == 123
```

**Testing query parameters:**
```python
def test_search_with_filters():
    response = client.get("/search?q=test&limit=5")
    assert response.status_code == 200
    assert len(response.json()["results"]) <= 5
```

**Testing error cases:**
```python
def test_item_not_found():
    response = client.get("/items/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
```

**See [references/testing.md](references/testing.md) for:**
- Complete pytest fundamentals and red-green cycle
- TestClient setup and fixtures
- Testing different request types (GET, POST, PUT, DELETE)
- Testing authentication and protected endpoints
- Overriding dependencies for testing
- Testing file uploads and forms
- Pytest fixtures and parametrization
- Async testing patterns
- Coverage reports and best practices
- Agent-specific testing considerations
- Complete working examples

## Lifespan Events

Your agent API needs resources ready before handling requests. Lifespan events let you run code at startup (before any request) and shutdown (after the last response).

**The lifespan pattern:**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Code here runs before first request
    print("Loading resources...")
    app.state.db_pool = create_db_pool()
    app.state.ml_model = load_model()
    yield  # Server runs and handles requests
    # SHUTDOWN: Code here runs after server stops
    print("Cleaning up...")
    await app.state.db_pool.dispose()
    del app.state.ml_model

app = FastAPI(lifespan=lifespan)
```

**Key concepts:**
- Everything before `yield` runs at startup
- Everything after `yield` runs at shutdown
- Use `app.state` to share resources with endpoints
- Access via `request.app.state` in endpoints
- Replace deprecated `@app.on_event()` decorator

**Common use cases:**
- Database connection pools
- Preloading ML models
- Initializing external API clients (httpx, Anthropic, OpenAI)
- Setting up caches

**Using shared resources in endpoints:**

```python
from fastapi import Request

@app.get("/users")
def list_users(request: Request):
    # Access resources from app.state
    db = request.app.state.db_pool
    cache = request.app.state.cache
    return db.query_users()
```

**See [references/lifespan-events.md](references/lifespan-events.md) for:**
- Complete lifespan implementation guide
- Database pool setup with SQLModel
- ML model preloading (avoid cold starts)
- External client initialization (httpx, Anthropic, OpenAI)
- Production-ready complete example
- Deprecated `@app.on_event()` comparison
- Common mistakes and best practices
- Why lifespan matters for agent APIs

## Streaming with SSE

Some operations take time. Streaming sends data as it becomes available—token by token for LLMs, update by update for long-running tasks. Essential for agent APIs where users need real-time feedback.

**Why streaming matters:**
- Users see responses forming in real-time
- Better perceived performance (first byte matters)
- Long operations show progress
- Failed operations fail fast

**Basic pattern:**

```python
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

async def task_updates_generator():
    for i in range(5):
        yield {
            "event": "task_update",
            "data": json.dumps({"progress": (i + 1) * 20})
        }
        await asyncio.sleep(1)
    yield {
        "event": "complete",
        "data": json.dumps({"message": "Done"})
    }

@app.get("/tasks/stream")
async def stream_task_updates():
    return EventSourceResponse(task_updates_generator())
```

**Key concepts:**
- Async generators use `yield` (not `return`)
- SSE data must be JSON string (use `json.dumps()`)
- Use `await asyncio.sleep()` not `time.sleep()` (non-blocking)
- `EventSourceResponse` handles SSE formatting
- Browser EventSource API for testing

**Why SSE over WebSockets:**
- Simpler (just HTTP with special content type)
- Works through proxies without configuration
- Browser handles reconnection automatically
- One-directional (perfect for server → client)

**Installation:**

```bash
uv add sse-starlette
```

**Testing in browser:**

```javascript
const eventSource = new EventSource('/tasks/stream');

eventSource.addEventListener('task_update', (event) => {
    const data = JSON.parse(event.data);
    console.log('Progress:', data.progress);
});

eventSource.addEventListener('complete', (event) => {
    console.log('Complete!');
    eventSource.close();
});
```

**Agent streaming example:**

```python
@app.get("/agent/think/stream")
async def stream_agent_thinking(query: str):
    async def thinking_stream():
        # Show thinking steps
        yield {
            "event": "thought",
            "data": json.dumps({"message": "Analyzing query..."})
        }
        await asyncio.sleep(1)

        # Stream response tokens
        response = "Based on analysis, here is the answer."
        for word in response.split():
            yield {
                "event": "token",
                "data": json.dumps({"token": word + " "})
            }
            await asyncio.sleep(0.1)

        # Completion
        yield {
            "event": "complete",
            "data": json.dumps({"done": True})
        }

    return EventSourceResponse(thinking_stream())
```

**Error handling in streams:**

```python
async def safe_stream():
    try:
        for i in range(10):
            yield {"event": "progress", "data": json.dumps({"step": i})}
            await asyncio.sleep(1)
    except Exception as e:
        # Send error as SSE event
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)})
        }
```

**Detect client disconnection:**

```python
from starlette.requests import Request

@app.get("/stream")
async def stream_with_disconnect(request: Request):
    async def generate():
        for i in range(100):
            if await request.is_disconnected():
                print("Client disconnected")
                break
            yield {"event": "message", "data": json.dumps({"count": i})}
            await asyncio.sleep(1)

    return EventSourceResponse(generate())
```

**See [references/streaming-sse.md](references/streaming-sse.md) for:**
- Complete SSE implementation guide
- Why streaming changes everything
- How SSE works (protocol details)
- Async generator patterns
- Browser EventSource API examples
- Testing with curl and JavaScript
- Error handling in streams
- Client disconnection detection
- Complete working examples
- Common mistakes (json.dumps, yield vs return, async sleep)
- Why SSE is perfect for agent APIs

## Agent Integration

Transform your FastAPI endpoints into callable tools for AI agents, enabling conversational access to your API operations. Your REST API becomes an AI-powered "digital employee."

**Why agent integration matters:**
- Natural language interface (no need to remember endpoints)
- Intelligent orchestration (agent decides which tools to call)
- Multi-step operations ("Create three tasks and mark the first one as done")
- Error recovery and graceful handling
- Digital FTE service (conversational access to capabilities)

**The integration pattern:**

```
API Endpoints → Tool Functions → @function_tool → Agent → Streaming Endpoint
```

**Basic pattern:**

```python
from agents import Agent, function_tool, Runner
from sse_starlette.sse import EventSourceResponse

# Step 1: Create tool function (wraps CRUD logic)
def create_task(title: str, description: str | None = None) -> dict:
    """Create a new task in the database."""
    with Session(engine) as session:
        task = Task(title=title, description=description)
        session.add(task)
        session.commit()
        session.refresh(task)
        return {"id": task.id, "title": task.title, "status": task.status}

# Step 2: Decorate with @function_tool for agent
@function_tool
def tool_create_task(title: str, description: str | None = None) -> str:
    """Create a new task with the given title and optional description."""
    result = create_task(title, description)
    return f"Created task {result['id']}: {result['title']}"

# Step 3: Build agent with tools
task_agent = Agent(
    name="Task Manager",
    instructions="Help users manage tasks. Create, list, update, and delete as requested.",
    tools=[tool_create_task, tool_list_tasks, tool_update_status, tool_delete_task]
)

# Step 4: Streaming endpoint
class ChatRequest(BaseModel):
    message: str

@app.post("/agent/chat/stream")
async def chat_with_agent_stream(request: ChatRequest):
    async def agent_stream():
        result = Runner.run_streamed(task_agent, request.message)

        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if hasattr(event.data, 'delta') and hasattr(event.data.delta, 'text'):
                    text = event.data.delta.text
                    if text:
                        yield {"event": "token", "data": json.dumps({"text": text})}

        yield {"event": "complete", "data": json.dumps({"response": result.final_output})}

    return EventSourceResponse(agent_stream())
```

**Installation:**

```bash
uv add openai-agents
```

**Environment variable:**

```bash
# .env
OPENAI_API_KEY=sk-your-api-key-here
```

**Key concepts:**

- **Tool functions** - Python functions that wrap CRUD operations, return JSON-serializable dicts
- **@function_tool** - Decorator that makes functions callable by agents
- **Docstrings** - Agent reads these to understand when to use each tool
- **Agent** - Orchestrates tools based on natural language instructions
- **Runner.run_streamed()** - Executes agent with streaming responses
- **Type hints required** - Agent needs to know parameter types

**Non-streaming endpoint:**

```python
@app.post("/agent/chat")
async def chat_with_agent(request: ChatRequest):
    result = await Runner.run(task_agent, request.message)
    return {"response": result.final_output}
```

**Testing with natural language:**

```bash
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a task called Learn FastAPI"}'

# Response: {"response": "Created task 1: Learn FastAPI"}

curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all my tasks"}'

# Response: {"response": "Found 1 tasks:\n- Task 1: Learn FastAPI (pending)"}
```

**Project structure:**

```
task-api/
├── tools.py      # CRUD functions (return dicts)
├── agent.py      # @function_tool wrappers and Agent
└── main.py       # FastAPI endpoints + agent endpoint
```

**Critical best practices:**

1. **Clear docstrings** - Agent relies on these to understand tool purpose
2. **Return dicts from tools** - Never return SQLModel instances (not JSON-serializable)
3. **Handle None/null cases** - Check if resource exists before accessing attributes
4. **Human-readable responses** - Format tool responses for conversation
5. **Type hints required** - Agent needs parameter types

**Common mistakes:**

```python
# ❌ WRONG - Missing docstring
@function_tool
def tool_create(title: str) -> str:
    return create_task(title)

# ✅ CORRECT - Clear docstring
@function_tool
def tool_create_task(title: str, description: str | None = None) -> str:
    """Create a new task with the given title and optional description."""
    result = create_task(title, description)
    return f"Created task {result['id']}: {result['title']}"

# ❌ WRONG - Returns SQLModel instance
def create_task(title: str) -> Task:
    return Task(title=title)  # Not serializable!

# ✅ CORRECT - Returns dict
def create_task(title: str) -> dict:
    task = Task(title=title)
    session.add(task)
    session.commit()
    return {"id": task.id, "title": task.title}
```

**Complete example with all CRUD operations:**

```python
# tools.py
def create_task(title: str, description: str | None = None) -> dict:
    # CRUD logic, returns dict

def list_tasks(status: str | None = None) -> dict:
    # CRUD logic, returns dict with task list

def update_task_status(task_id: int, status: str) -> dict:
    # CRUD logic, returns dict with success/error

def delete_task(task_id: int) -> dict:
    # CRUD logic, returns dict with success/error

# agent.py
from agents import Agent, function_tool
from tools import create_task, list_tasks, update_task_status, delete_task

@function_tool
def tool_create_task(title: str, description: str | None = None) -> str:
    """Create a new task with the given title and optional description."""
    result = create_task(title, description)
    return f"Created task {result['id']}: {result['title']}"

@function_tool
def tool_list_tasks(status: str | None = None) -> str:
    """List all tasks, optionally filtered by status (pending, in_progress, completed)."""
    result = list_tasks(status)
    if result["count"] == 0:
        return "No tasks found."
    tasks_str = "\n".join([f"- Task {t['id']}: {t['title']} ({t['status']})" for t in result["tasks"]])
    return f"Found {result['count']} tasks:\n{tasks_str}"

@function_tool
def tool_update_status(task_id: int, status: str) -> str:
    """Update a task's status. Status must be: pending, in_progress, or completed."""
    result = update_task_status(task_id, status)
    if not result.get("success"):
        return f"Error: {result['error']}"
    return f"Updated task {task_id} to status: {status}"

@function_tool
def tool_delete_task(task_id: int) -> str:
    """Delete a task by ID."""
    result = delete_task(task_id)
    if not result.get("success"):
        return f"Error: {result['error']}"
    return result["message"]

task_agent = Agent(
    name="Task Manager",
    instructions="""You are a helpful task management assistant.

You can create, list, update status, and delete tasks.
Always be conversational and confirm what you've done.
If a task ID is needed but not provided, list tasks first.""",
    tools=[tool_create_task, tool_list_tasks, tool_update_status, tool_delete_task]
)
```

**See [references/agent-integration.md](references/agent-integration.md) for:**
- Complete agent integration guide
- Why agent integration transforms APIs
- Creating tool functions from CRUD operations
- Decorating with @function_tool
- Building agents with instructions
- Streaming vs non-streaming endpoints
- Complete working example with all files
- Hands-on exercise
- Common mistakes (missing docstrings, complex return types, null handling)
- Best practices for production agent APIs

## Background Tasks

Run tasks after sending responses:

```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    # Send email
    pass

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, email, "notification")
    return {"message": "Notification sent in the background"}
```

**See [references/background-tasks.md](references/background-tasks.md) for:**
- Email notifications
- File processing
- Webhooks
- Database cleanup
- Audit logging
- When to use Celery instead

## Production Deployment

Deploy with Uvicorn and Gunicorn:

```bash
# Development
fastapi dev app/main.py

# Production
fastapi run app/main.py --port 8000 --workers 4

# With Gunicorn
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

**See [references/deployment.md](references/deployment.md) for:**
- Production server setup
- Worker configuration
- Docker deployment
- Environment configuration
- HTTPS and reverse proxy
- Performance optimization
- Monitoring and logging
- Systemd service setup

## Project Structure

Recommended structure for production applications:

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # Settings
│   ├── routers/             # API routes
│   │   ├── users.py
│   │   └── items.py
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── dependencies/        # Shared dependencies
├── tests/                   # Test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Common Workflows

### Building a Simple API

1. Start with hello-world template from `assets/hello-world/`
2. Add path operations in `main.py`
3. Define Pydantic models for validation
4. Add error handling with `HTTPException`
5. Test with interactive docs at `/docs`

### Building a Production API

1. Use `scripts/create_project.py` or copy `assets/production-template/`
2. Configure environment in `.env`
3. Define schemas in `app/schemas/`
4. Create routers in `app/routers/`
5. Add dependencies in `app/dependencies/`
6. Implement business logic in `app/services/`
7. Write tests in `tests/`
8. Deploy with Docker or Gunicorn

### Adding Authentication

1. See [references/security.md](references/security.md) for complete examples
2. For JWT: Install `python-jose` and `passlib`
3. Create OAuth2 scheme and password hashing
4. Implement token creation and validation
5. Add dependency for current user
6. Protect routes with authentication dependency

### Adding Database Integration

1. Install SQLAlchemy: `pip install sqlalchemy`
2. Create database models in `app/models/`
3. Create database dependency with yield:
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
4. Use in path operations:
```python
@app.get("/users/")
async def read_users(db: Annotated[Session, Depends(get_db)]):
    return db.query(User).all()
```

### Adding CORS

1. Import and configure middleware (see [references/middleware-cors.md](references/middleware-cors.md))
2. Specify allowed origins (never use `["*"]` with `allow_credentials=True`)
3. Configure allowed methods and headers
4. Test from browser console

## Development Tips

### Auto-Reload During Development

```bash
fastapi dev app/main.py
```

The `fastapi dev` command automatically:
- Enables hot-reload
- Uses port 8000
- Shows detailed error messages
- Enables debug mode

### Interactive API Documentation

FastAPI automatically generates:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI schema**: `http://localhost:8000/openapi.json`

Use Swagger UI to test endpoints directly in the browser.

### Type Hints for Editor Support

Always use type hints for:
- Better editor autocompletion
- Automatic validation
- Auto-generated documentation

```python
# Good
@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    pass

# Missing benefits without type hints
@app.get("/items/{item_id}")
async def read_item(item_id, q=None):
    pass
```

### Async vs Sync

Use `async def` when:
- Using `await` (database queries, HTTP requests)
- I/O-bound operations

Use regular `def` when:
- CPU-bound operations
- Blocking libraries

FastAPI handles both correctly.

## Debugging

### Enable Debug Mode

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

### Check Request/Response

```python
from fastapi import Request

@app.get("/debug")
async def debug(request: Request):
    return {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
    }
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

@app.get("/items/")
async def read_items():
    logger.info("Reading items")
    return items
```

## Reference Documentation

For detailed information on specific topics:

- **[path-operations.md](references/path-operations.md)** - Path params, query params, request/response handling
- **[crud-operations.md](references/crud-operations.md)** - Complete CRUD operations guide, HTTP method semantics
- **[error-handling.md](references/error-handling.md)** - HTTPException, status codes, error message design
- **[dependencies.md](references/dependencies.md)** - Dependency injection patterns
- **[security.md](references/security.md)** - Authentication and authorization
- **[middleware-cors.md](references/middleware-cors.md)** - Middleware and CORS configuration
- **[testing.md](references/testing.md)** - Testing with TestClient and pytest
- **[background-tasks.md](references/background-tasks.md)** - Background task patterns
- **[deployment.md](references/deployment.md)** - Production deployment guide

## Scripts

- **[scripts/create_project.py](scripts/create_project.py)** - Scaffold new FastAPI projects
- **[scripts/start_dev.sh](scripts/start_dev.sh)** - Start development server

## Assets

- **[assets/hello-world/](assets/hello-world/)** - Minimal FastAPI application
- **[assets/production-template/](assets/production-template/)** - Production-ready project structure

## Key Principles

1. **Always use type hints for path and query parameters** - Type hints enable automatic validation, better error messages, API documentation generation, and editor autocompletion. Never omit type hints on function parameters.
   ```python
   # ✓ GOOD - Type hints provide validation and docs
   @app.get("/items/{item_id}")
   async def get_item(item_id: int, limit: int = 10, q: str | None = None):
       return {"item_id": item_id, "limit": limit, "query": q}

   # ✗ BAD - Missing type hints loses validation and documentation
   @app.get("/items/{item_id}")
   async def get_item(item_id, limit=10, q=None):
       return {"item_id": item_id, "limit": limit, "query": q}
   ```

2. **Always return dictionaries, never None** - Endpoints should always return valid JSON-serializable data. Return empty dictionaries `{}` or meaningful default responses instead of None.
   ```python
   # ✓ GOOD - Returns valid JSON response
   @app.delete("/items/{item_id}")
   async def delete_item(item_id: int):
       delete_from_db(item_id)
       return {"status": "deleted", "item_id": item_id}

   # ✗ BAD - Returning None causes issues
   @app.delete("/items/{item_id}")
   async def delete_item(item_id: int):
       delete_from_db(item_id)
       return None
   ```

3. **Use descriptive function names matching endpoint purpose** - Function names should clearly describe what the endpoint does, not just the HTTP method. This improves code readability and generated documentation.
   ```python
   # ✓ GOOD - Clear, purpose-driven names
   @app.get("/users/{user_id}")
   async def get_user(user_id: int):
       return {"user_id": user_id}

   @app.post("/users/")
   async def create_user(user: User):
       return user

   @app.get("/search")
   async def search_items(q: str, limit: int = 10):
       return {"query": q, "results": []}

   # ✗ BAD - Generic names don't convey purpose
   @app.get("/users/{user_id}")
   async def handler1(user_id: int):
       return {"user_id": user_id}

   @app.post("/users/")
   async def endpoint(user: User):
       return user
   ```

4. **Always use uv package manager for project setup** - Use [uv](https://docs.astral.sh/uv/) for creating and managing FastAPI projects. Install FastAPI with: `uv add "fastapi[standard]"` which includes uvicorn, pydantic, and other essential dependencies.

5. **Pydantic for data validation** - Use Pydantic models for request/response validation and automatic documentation generation.

6. **Dependencies for reuse** - Leverage FastAPI's dependency injection system to avoid code repetition and improve testability. Use `Depends()` to share configuration, database connections, and authentication logic across endpoints. Use `@lru_cache` for expensive, static dependencies (like configuration). Use `yield` in dependencies that need cleanup (like database sessions). Remember: pass the function to `Depends()`, don't call it.

7. **Test with TestClient** - Write tests using FastAPI's TestClient for easy, fast endpoint testing without running a server.

8. **Environment variables for configuration** - Never hardcode secrets, API keys, or environment-specific settings. Use pydantic-settings with BaseSettings for type-safe configuration. Always add `.env` to `.gitignore` and create `.env.example` as a template. Cache settings with `@lru_cache` on `get_settings()` function. Use `Depends(get_settings)` for dependency injection.

9. **Structure matters as projects grow** - Start simple, but organize code into routers, schemas, services, and dependencies as the project grows.

10. **Consult official documentation** - FastAPI has excellent documentation at https://fastapi.tiangolo.com - always reference it for advanced patterns and best practices.

11. **CRUD operations are the foundation** - Master Create, Read, Update, Delete operations to build data-driven APIs. Every agent that manages state needs CRUD. Use proper HTTP methods (GET for read, POST for create, PUT for update, DELETE for delete) with correct semantics. GET is safe and cacheable, PUT/DELETE are idempotent and can be safely retried on failure.

12. **Handle errors explicitly with HTTPException** - Always raise HTTPException for HTTP errors (not Python exceptions). Use status module constants (status.HTTP_404_NOT_FOUND) for readability. Return appropriate status codes: 404 for not found, 400 for business rule violations, 422 for schema validation (automatic). Design error messages that are helpful for both humans and agents, including context about what went wrong and what's valid.

## Common Issues

### Import Errors

Ensure proper package structure with `__init__.py` files in all packages.

### CORS Errors

Configure CORS middleware with specific origins, not `["*"]` in production.

### Validation Errors (422)

Check Pydantic models - FastAPI validates request data automatically.

### Database Connection Errors

Use dependencies with `yield` for proper connection management.

### Deployment Issues

- Set `DEBUG=False` in production
- Use multiple workers for production
- Configure proper CORS origins
- Use environment variables for secrets

## Troubleshooting uv and Project Setup

### uv command not found

**Problem**: `bash: uv: command not found`

**Solution**: Install uv:
```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

### Cannot run fastapi dev - UnicodeEncodeError

**Problem**: `UnicodeEncodeError: 'charmap' codec can't encode character`

**Solution**: Use uvicorn directly:
```bash
# Instead of: fastapi dev main.py
# Use:
uv run uvicorn main:app --reload
```

### pyproject.toml not found

**Problem**: Running commands outside uv project

**Solution**: Always create a uv project first:
```bash
uv init my-project
cd my-project
uv add "fastapi[standard]"
# Now create your code files
```

### ImportError: No module named 'fastapi'

**Problem**: Dependencies not installed or wrong environment

**Solution**: Ensure you're using uv run:
```bash
# Install dependencies
uv add "fastapi[standard]"

# Run with uv (uses correct virtual environment)
uv run uvicorn main:app --reload

# NOT: python main.py  (uses wrong Python)
```

### Virtual environment issues

**Problem**: Packages not found even after installation

**Solution**: Always prefix commands with `uv run`:
```bash
uv run pytest          # NOT: pytest
uv run python main.py  # NOT: python main.py
uv run uvicorn main:app  # NOT: uvicorn main:app
```

### Stale lock file

**Problem**: Dependencies out of sync

**Solution**: Update the lock file:
```bash
uv lock --upgrade
uv sync
```

### Missing standard dependencies

**Problem**: uvicorn, pydantic, etc. not installed

**Solution**: Always use `fastapi[standard]`:
```bash
# CORRECT
uv add "fastapi[standard]"

# WRONG - missing dependencies
uv add fastapi
```

# Dependency Injection Reference

Complete guide to FastAPI's dependency injection system for code reuse, database connections, authentication, and more.

## Table of Contents
- What is Dependency Injection
- The Problem: Repeated Setup
- Basic Dependencies
- A Dependency Is Just a Function
- Sharing Dependencies with Annotated
- Classes as Dependencies
- Caching with lru_cache
- Sub-dependencies
- Dependencies in Path Operation Decorators
- Global Dependencies
- Dependencies with Yield
- Why This Matters
- Hands-On Exercise
- Common Mistakes
- Try With AI

## What is Dependency Injection

Dependency Injection means path operation functions can declare requirements, and FastAPI automatically provides them.

**Use cases:**
- Shared logic and code reuse
- Database connections
- Security and authentication
- Permission/role requirements
- Data validation
- Minimizing code repetition

## The Problem: Repeated Setup

Without dependency injection, you end up repeating setup code in every endpoint:

```python
@app.get("/tasks")
def list_tasks():
    # Setup code repeated in EVERY endpoint
    config = load_config_from_env()
    logger = setup_logger("tasks")
    return {"config": config.app_name}

@app.get("/users")
def list_users():
    # Same setup, repeated again
    config = load_config_from_env()
    logger = setup_logger("users")
    return {"config": config.app_name}
```

**Problems:**

* Same code in every function
* Hard to test (can't swap config for test config)
* If setup logic changes, you update everywhere

**The Solution: Depends()**

With dependency injection:

```python
from fastapi import FastAPI, Depends

app = FastAPI()

def get_config():
    """Provide configuration to endpoints."""
    return {"app_name": "Task API", "version": "1.0"}

@app.get("/tasks")
def list_tasks(config: dict = Depends(get_config)):
    return {"app": config["app_name"]}

@app.get("/users")
def list_users(config: dict = Depends(get_config)):
    return {"app": config["app_name"]}
```

FastAPI:

* Sees `Depends(get_config)`
* Calls `get_config()` automatically
* Passes the result to your function

**Output:**

```json
{"app": "Task API"}
```

## Basic Dependencies

### Creating a Dependency

A dependency is a function that accepts the same parameter types as path operations:

```python
from typing import Annotated
from fastapi import Depends, FastAPI

app = FastAPI()

async def common_parameters(
    q: str | None = None,
    skip: int = 0,
    limit: int = 100
):
    return {"q": q, "skip": skip, "limit": limit}
```

### Using Dependencies

Use `Depends()` to declare dependencies:

```python
@app.get("/items/")
async def read_items(commons: Annotated[dict, Depends(common_parameters)]):
    return commons

@app.get("/users/")
async def read_users(commons: Annotated[dict, Depends(common_parameters)]):
    return commons
```

**Important:** Pass the function to `Depends()` without calling it (no parentheses).

## A Dependency Is Just a Function

Any callable works as a dependency:

```python
def get_request_id() -> str:
    """Generate unique ID for this request."""
    import uuid
    return str(uuid.uuid4())

@app.get("/debug")
def debug_info(request_id: str = Depends(get_request_id)):
    return {"request_id": request_id}
```

**Output:**

```json
{"request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}
```

Each request gets a new UUID. The dependency runs fresh for every request.

## Sharing Dependencies with Annotated

Reduce duplication by storing dependencies as type aliases:

```python
from typing import Annotated
from fastapi import Depends

CommonsDep = Annotated[dict, Depends(common_parameters)]

@app.get("/items/")
async def read_items(commons: CommonsDep):
    return commons

@app.get("/users/")
async def read_users(commons: CommonsDep):
    return commons
```

**Benefits:**
- Single source of truth
- Preserves type information
- Editor autocompletion works
- Compatible with type checkers like mypy

## Classes as Dependencies

Classes can be used as dependencies for stateful logic:

```python
from typing import Annotated
from fastapi import Depends

class CommonQueryParams:
    def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit

@app.get("/items/")
async def read_items(commons: Annotated[CommonQueryParams, Depends(CommonQueryParams)]):
    response = {}
    if commons.q:
        response.update({"q": commons.q})
    response.update({"skip": commons.skip, "limit": commons.limit})
    return response
```

**Shortcut when class and type are the same:**

```python
@app.get("/items/")
async def read_items(commons: Annotated[CommonQueryParams, Depends()]):
    return commons
```

## Caching with lru_cache

Some dependencies are expensive—reading config files, creating connections. You want them created once, not per-request:

```python
from functools import lru_cache

@lru_cache
def get_settings():
    """Load settings once, reuse forever."""
    print("Loading settings...")  # Only prints once!
    return {
        "app_name": "Task API",
        "debug": True
    }

@app.get("/info")
def app_info(settings: dict = Depends(get_settings)):
    return {"app": settings["app_name"]}
```

Call `/info` ten times—you'll see "Loading settings..." printed only once.

**When to use @lru_cache:**

* Configuration that doesn't change
* Expensive initialization (parsing files, creating clients)
* Anything you'd normally put in a global variable

**When NOT to use @lru_cache:**

* Per-request values (like request IDs)
* Data that needs to be fresh each time
* Stateful dependencies that change between requests

## Sub-dependencies

Dependencies can have their own dependencies, creating a tree:

```python
from fastapi import Cookie

def query_extractor(q: str | None = None):
    return q

def query_or_cookie_extractor(
    q: Annotated[str, Depends(query_extractor)],
    last_query: Annotated[str | None, Cookie()] = None
):
    if not q:
        return last_query
    return q

@app.get("/items/")
async def read_query(
    query_or_default: Annotated[str, Depends(query_or_cookie_extractor)]
):
    return {"q_or_cookie": query_or_default}
```

**How it works:**
1. FastAPI calls `query_extractor`
2. Result passed to `query_or_cookie_extractor`
3. Final result passed to `read_query`

## Common Dependency Patterns

### Database Session

```python
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/")
async def read_users(db: Annotated[Session, Depends(get_db)]):
    users = db.query(User).all()
    return users
```

### Current User

```python
from fastapi import HTTPException, Header

async def get_token_header(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")
    return x_token

async def get_current_user(token: Annotated[str, Depends(get_token_header)]):
    # Validate token and get user
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return user

@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
```

### Pagination

```python
def pagination_params(skip: int = 0, limit: int = 100):
    return {"skip": skip, "limit": limit}

PaginationDep = Annotated[dict, Depends(pagination_params)]

@app.get("/items/")
async def read_items(pagination: PaginationDep):
    return fake_items_db[pagination["skip"]:pagination["skip"] + pagination["limit"]]
```

### Settings as Dependency

Environment variables are commonly used with dependency injection:

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "Task API"
    debug: bool = False

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()

@app.get("/info")
def app_info(settings: Settings = Depends(get_settings)):
    return {"app_name": settings.app_name}
```

See [references/environment-variables.md](environment-variables.md) for complete guide.

## Dependencies in Path Operation Decorators

For dependencies that don't return values (side effects only):

```python
from fastapi import Depends, HTTPException

async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key

@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]
```

**Use case:** Authentication/validation without using the result.

## Global Dependencies

Apply dependencies to all path operations:

```python
app = FastAPI(dependencies=[Depends(verify_token), Depends(verify_key)])
```

Or to a router:

```python
from fastapi import APIRouter

router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(verify_token)]
)

@router.get("/")
async def read_items():
    return [{"item": "Foo"}]
```

## Dependencies with Yield

Use `yield` for setup/teardown logic (e.g., database connections):

```python
async def get_db():
    db = SessionLocal()
    try:
        yield db  # This is injected into path operation
    finally:
        db.close()  # Cleanup after response is sent

@app.get("/users/")
async def read_users(db: Annotated[Session, Depends(get_db)]):
    users = db.query(User).all()
    return users
```

**Execution flow:**
1. Code before `yield` runs before request processing
2. Yielded value is injected
3. Path operation executes
4. Code after `yield` runs after response is sent

Some resources need cleanup—file handles, connections, temporary files. Use `yield` instead of `return`:

```python
def get_temp_file():
    """Provide a temporary file that gets cleaned up."""
    import tempfile
    import os

    # Setup: create the file
    fd, path = tempfile.mkstemp()
    file = os.fdopen(fd, 'w')

    try:
        yield file  # Provide to endpoint
    finally:
        # Cleanup: runs after endpoint completes
        file.close()
        os.unlink(path)

@app.post("/upload")
def process_upload(temp: file = Depends(get_temp_file)):
    temp.write("data")
    return {"status": "processed"}
```

The `finally` block runs after your endpoint finishes—even if it raises an exception. This is how database sessions will work in later lessons.

**Complete Example: Request Logger**

Here's a practical dependency that logs every request:

```python
from fastapi import FastAPI, Depends, Request
from datetime import datetime

app = FastAPI()

def get_request_logger(request: Request):
    """Log request details and provide logger to endpoint."""
    start = datetime.now()
    method = request.method
    path = request.url.path

    print(f"[{start}] {method} {path} - started")

    yield {"method": method, "path": path, "start": start}

    end = datetime.now()
    duration = (end - start).total_seconds()
    print(f"[{end}] {method} {path} - completed in {duration:.3f}s")

@app.get("/tasks")
def list_tasks(log: dict = Depends(get_request_logger)):
    return {"tasks": [], "logged_path": log["path"]}

@app.post("/tasks")
def create_task(log: dict = Depends(get_request_logger)):
    return {"id": 1, "logged_method": log["method"]}
```

**Console output:**

```
[2024-01-15 10:30:00] GET /tasks - started
[2024-01-15 10:30:00] GET /tasks - completed in 0.002s
```

Notice how `Request` is also injected—FastAPI provides it automatically.

### Yield with Try/Except

```python
async def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

### Sub-dependencies with Yield

```python
async def dependency_a():
    print("dependency_a: start")
    dep_a = {"value": "from dependency_a"}
    yield dep_a
    print("dependency_a: cleanup")

async def dependency_b(dep_a: Annotated[dict, Depends(dependency_a)]):
    print("dependency_b: start")
    dep_b = {"value": "from dependency_b", "parent": dep_a}
    yield dep_b
    print("dependency_b: cleanup")

@app.get("/")
async def read_main(dep_b: Annotated[dict, Depends(dependency_b)]):
    return dep_b
```

**Execution order:**
1. `dependency_a` start
2. `dependency_b` start
3. Path operation
4. `dependency_b` cleanup
5. `dependency_a` cleanup

## Why This Matters

Dependency injection powers everything in the rest of this chapter. Understanding `Depends()` now means these patterns will make sense immediately.

In the next lessons, you'll use `Depends()` for:

| Lesson | Dependency | Purpose |
|--------|------------|---------|
| Environment Variables | `get_settings()` | Configuration from .env |
| SQLModel | `get_session()` | Database connection |
| Authentication | `get_current_user()` | Verify JWT tokens |

All of these follow the same pattern you learned here.

## Async Considerations

You can mix `async def` and `def` dependencies freely:

```python
async def async_dependency():
    # Can use await
    return {"key": "value"}

def sync_dependency():
    # Regular function
    return {"key": "value"}

@app.get("/async-path/")
async def async_path(
    dep1: Annotated[dict, Depends(async_dependency)],
    dep2: Annotated[dict, Depends(sync_dependency)]
):
    return {"dep1": dep1, "dep2": dep2}

@app.get("/sync-path/")
def sync_path(
    dep1: Annotated[dict, Depends(async_dependency)],
    dep2: Annotated[dict, Depends(sync_dependency)]
):
    return {"dep1": dep1, "dep2": dep2}
```

FastAPI handles the execution appropriately.

## Hands-On Exercise

Build a simple API with dependencies:

**Step 1: Create the app with a config dependency:**

```python
from fastapi import FastAPI, Depends
from functools import lru_cache

app = FastAPI()

@lru_cache
def get_config():
    return {
        "app_name": "My API",
        "max_items": 100,
        "debug": True
    }

@app.get("/config")
def show_config(config: dict = Depends(get_config)):
    return config
```

**Step 2: Add a request counter (using a class for state):**

```python
class RequestCounter:
    def __init__(self):
        self.count = 0

    def increment(self) -> int:
        self.count += 1
        return self.count

counter = RequestCounter()

def get_request_count() -> int:
    return counter.increment()

@app.get("/count")
def show_count(count: int = Depends(get_request_count)):
    return {"request_number": count}
```

**Step 3: Test it:**

```bash
# First request
curl http://localhost:8000/count
# {"request_number": 1}

# Second request
curl http://localhost:8000/count
# {"request_number": 2}
```

**Step 4: Add a dependency with cleanup:**

```python
def get_request_id():
    """Generate unique ID per request."""
    import uuid
    request_id = str(uuid.uuid4())
    print(f"Request started: {request_id}")

    yield request_id

    print(f"Request completed: {request_id}")

@app.get("/debug")
def debug_info(request_id: str = Depends(get_request_id)):
    return {"request_id": request_id}
```

## Common Mistakes

**Mistake 1: Calling the function instead of passing it**

```python
# Wrong - function called at import time!
@app.get("/tasks")
def list_tasks(config = Depends(get_config())):  # () is wrong!
    ...

# Correct - pass the function itself
@app.get("/tasks")
def list_tasks(config = Depends(get_config)):  # No ()
    ...
```

**Mistake 2: Forgetting to yield in cleanup dependencies**

```python
# Wrong - return doesn't allow cleanup code
def get_file():
    f = open("data.txt")
    return f  # File never closed!

# Correct - yield allows cleanup
def get_file():
    f = open("data.txt")
    try:
        yield f
    finally:
        f.close()
```

**Mistake 3: Caching things that should be fresh**

```python
# Wrong - request ID should be different each time!
@lru_cache
def get_request_id():
    return str(uuid.uuid4())

# Correct - no cache for per-request values
def get_request_id():
    return str(uuid.uuid4())
```

**Mistake 4: Not understanding when dependencies run**

```python
# Dependencies run for EVERY request
# Don't put expensive operations without caching

# Wrong - parses config file every request
def get_config():
    return parse_config_file()  # Expensive!

# Correct - cache expensive operations
@lru_cache
def get_config():
    return parse_config_file()  # Only runs once
```

## Try With AI

After completing the exercise, explore these patterns.

**Prompt 1: Dependency Chains**

```
I have a config dependency and want to create a logger dependency
that uses the config. How do dependencies depend on other dependencies?
Show me how to chain get_logger(config = Depends(get_config)).
```

**What you're learning:** Dependencies can depend on other dependencies. FastAPI resolves the chain automatically.

**Prompt 2: Testing Dependencies**

```
I want to test my endpoints without using the real config.
How do I override a dependency in tests? Show me
app.dependency_overrides and how to use it.
```

**What you're learning:** The power of DI is testability. Override any dependency with a mock for testing.

**Prompt 3: Class Dependencies**

```
Instead of functions, can I use a class as a dependency?
I want TaskService with methods like list() and create().
Show me how Depends() works with classes.
```

**What you're learning:** Classes with `__init__` parameters work as dependencies. FastAPI resolves the constructor parameters.

## Key Points

- Dependencies are regular functions with the same parameters as path operations
- Use `Depends()` to declare dependencies
- Store shared dependencies in `Annotated` type aliases
- Dependencies can have sub-dependencies (tree structure)
- Use `yield` for setup/teardown logic
- Dependencies execute automatically for every request
- All validation and documentation benefits apply to dependencies
- Mix `async` and `sync` dependencies freely

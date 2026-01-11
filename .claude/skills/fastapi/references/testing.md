# Testing Reference

Complete guide to testing FastAPI applications with TestClient and pytest, including fundamentals of test-driven development and agent-specific considerations.

## Table of Contents
- Why Write Tests Manually First?
- Why Testing Matters for Agent APIs
- The Red-Green Cycle (TDD Fundamentals)
- Setup and Installation
- Basic Testing with TestClient
- Testing Different Request Types
- Testing CRUD Operations
- Testing Error Handling
- Testing Authentication
- Testing Dependencies
- Testing File Uploads
- Testing WebSockets
- Async Tests
- Test Organization
- Agent-Specific Testing Considerations
- Common Mistakes and Solutions

---

## Why Write Tests Manually First?

**Testing isn't something you add later—it's how you verify your code does what you think it does.**

Before you ask AI to help generate tests, you need to understand testing fundamentals yourself:

### You Need to Recognize Good Tests from Bad Ones

When AI suggests a test, you need to evaluate:
- Does this test actually verify the behavior?
- Is this testing implementation or interface?
- Will this test catch regressions?
- Is this test too brittle or too broad?

**You can't evaluate AI suggestions if you've never written tests yourself.**

### You Need to Know What a Failing Test Tells You

A failing test is information:
- RED means "this doesn't exist yet" (TDD)
- RED means "I broke something" (regression)
- RED means "my assumptions were wrong" (design feedback)

When AI-generated tests fail, you need to interpret WHY, not just make them green.

### You Need Hands-On Experience

Like learning to drive, you can't just read about it:
- Write tests that fail for the wrong reasons
- Write tests that pass for the wrong reasons
- Experience the pain of brittle tests
- Feel the confidence of good test coverage

**By the end of this guide, every endpoint you build will have tests—and you'll know why.**

---

## Why Testing Matters for Agent APIs

FastAPI is commonly used to build APIs for AI agents. Testing is CRITICAL for agent-facing APIs:

### Agents Can't Guess

- Agents call exactly what your API exposes
- No documentation mismatch
- No hand-waving about "expected" behavior
- If your API says it returns `{"status": "ok"}`, that's what the agent expects
- If you return `{"status": "success"}` instead, the agent breaks

### Errors Cascade

- A broken endpoint breaks every agent that uses it
- One failing endpoint can take down entire workflows
- Agents don't adapt—they fail fast and loud
- Your API is a contract: break it, and everything downstream breaks

### Debugging is Hard

- Agent failures often trace back to subtle API changes
- "It works in Postman" doesn't mean it works for agents
- Agents chain multiple API calls—debugging multi-step failures is painful
- Tests catch these issues before agents do

### Confidence Enables Iteration

- Tests let you refactor without fear
- You can improve your code knowing nothing broke
- Change response formats safely
- Add features without breaking existing functionality
- Deploy confidently, knowing your contract holds

**If you're building APIs for agents, untested code is a time bomb.**

---

## The Red-Green Cycle (TDD Fundamentals)

Test-Driven Development (TDD) follows a simple, powerful rhythm:

### The Three-Step Rhythm

1. **RED** - Write a failing test (test something that doesn't exist yet)
2. **GREEN** - Make it pass (write the minimum code to pass)
3. **REFACTOR** - Clean up your code (while tests stay green)

This cycle forces you to:
- **Think about the interface before implementation**
- **Write only the code you need**
- **Refactor fearlessly with tests as a safety net**

### Practical Example: Building a `/health` Endpoint

Let's build a health check endpoint using TDD.

#### Step 1: Write a Failing Test (RED)

**tests/test_main.py:**
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint_exists():
    """The /health endpoint should exist."""
    response = client.get("/health")
    assert response.status_code == 200

def test_health_returns_operational_status():
    """The /health endpoint should return operational status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
```

**Run the test:**
```bash
uv run pytest tests/test_main.py -v
```

**Output (RED):**
```
tests/test_main.py::test_health_endpoint_exists FAILED
tests/test_main.py::test_health_returns_operational_status FAILED

============ FAILURES ============
_ test_health_endpoint_exists _
E   assert 404 == 200
E   404: Not Found
```

**❌ RED - Good! The endpoint doesn't exist yet.**

#### Step 2: Make It Pass (GREEN)

**main.py:**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def get_health_status():
    """Health check endpoint."""
    return {"status": "operational"}
```

**Run the test again:**
```bash
uv run pytest tests/test_main.py -v
```

**Output (GREEN):**
```
tests/test_main.py::test_health_endpoint_exists PASSED
tests/test_main.py::test_health_returns_operational_status PASSED

====== 2 passed in 0.12s ======
```

**✅ GREEN - Success! Tests pass.**

#### Step 3: Refactor (While Staying Green)

Now improve the endpoint with more details:

**main.py:**
```python
from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.get("/health")
async def get_health_status():
    """
    Health check endpoint with detailed information.

    Returns operational status, version, and timestamp.
    """
    return {
        "status": "operational",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "task-api"
    }
```

**Run tests again:**
```bash
uv run pytest tests/test_main.py -v
```

**Still GREEN! ✅**

The tests still pass because we added fields without breaking the existing contract. If you need to test the new fields, add new tests.

### Benefits of the Red-Green Cycle

1. **RED first forces interface thinking** - You design the API before implementing it
2. **GREEN ensures progress** - You always have working code
3. **REFACTOR with confidence** - Tests catch regressions immediately
4. **No over-engineering** - Write only what's needed to pass tests
5. **Living documentation** - Tests show how your API should be used

**Tip:** Commit on GREEN, not on RED. Always leave your codebase in a passing state.

---

## Table of Contents
- Setup and Installation
- Basic Testing with TestClient
- Testing Different Request Types
- Testing Authentication
- Testing Dependencies
- Testing File Uploads
- Testing WebSockets
- Async Tests
- Test Organization

## Setup and Installation

### Install Testing Dependencies

Always use `uv` to install pytest as a development dependency:

```bash
uv add --dev pytest
```

**Note:** `httpx` (required by TestClient) is already included with `fastapi[standard]`, so you don't need to install it separately.

### Verify Installation

```bash
uv run pytest --version
```

Expected output:
```
pytest 8.x.x
```

### Project Structure

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── routers/
│       └── items.py
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   └── test_items.py
├── pytest.ini
└── requirements.txt
```

### pytest.ini Configuration

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## Basic Testing with TestClient

### Simple Test

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/")
async def read_main():
    return {"msg": "Hello World"}

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}
```

**Key points:**
- Use regular `def`, not `async def`
- Use regular calls, not `await`
- TestClient follows pytest conventions

### Testing with Separate Files

**app/main.py:**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_main():
    return {"msg": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**tests/test_main.py:**
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
```

## Testing Different Request Types

### GET Requests

```python
def test_get_item():
    response = client.get("/items/1")
    assert response.status_code == 200
    assert response.json() == {"item_id": 1, "name": "Item 1"}

def test_get_with_query_params():
    response = client.get("/items/?skip=0&limit=10")
    assert response.status_code == 200
    assert len(response.json()) <= 10
```

### POST Requests

```python
def test_create_item():
    response = client.post(
        "/items/",
        json={"name": "Foo", "price": 45.2}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Foo"
    assert response.json()["price"] == 45.2
```

### PUT Requests

```python
def test_update_item():
    response = client.put(
        "/items/1",
        json={"name": "Updated Item", "price": 99.9}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Item"
```

### DELETE Requests

```python
def test_delete_item():
    response = client.delete("/items/1")
    assert response.status_code == 204

def test_delete_nonexistent_item():
    response = client.delete("/items/999")
    assert response.status_code == 404
```

### Testing with Headers

```python
def test_with_custom_header():
    response = client.get(
        "/items/",
        headers={"X-Token": "test-token"}
    )
    assert response.status_code == 200
```

### Testing with Cookies

```python
def test_with_cookies():
    response = client.get(
        "/items/",
        cookies={"session_id": "abc123"}
    )
    assert response.status_code == 200
```

## Testing CRUD Operations

### Complete CRUD Test Suite

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_task():
    """POST /tasks creates a new task."""
    response = client.post(
        "/tasks",
        json={"title": "Test task", "description": "Test description"}
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Test task"
    assert response.json()["status"] == "pending"

def test_list_tasks():
    """GET /tasks returns all tasks."""
    response = client.get("/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_tasks_filtered():
    """GET /tasks?status=pending filters correctly."""
    # Create tasks with different statuses
    client.post("/tasks", json={"title": "Pending task"})
    client.post("/tasks", json={"title": "Another task"})

    # Update one to completed
    client.put("/tasks/1", json={"title": "Pending task", "status": "completed"})

    # Filter for pending
    response = client.get("/tasks?status=pending")
    assert response.status_code == 200
    tasks = response.json()
    assert all(task["status"] == "pending" for task in tasks)

def test_get_task():
    """GET /tasks/{id} returns single task."""
    # Create first
    create_response = client.post("/tasks", json={"title": "Fetch me"})
    task_id = create_response.json()["id"]

    # Then fetch
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Fetch me"

def test_get_task_not_found():
    """GET /tasks/{id} returns 404 for missing task."""
    response = client.get("/tasks/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_update_task():
    """PUT /tasks/{id} updates a task."""
    # Create first
    create_response = client.post("/tasks", json={"title": "Original"})
    task_id = create_response.json()["id"]

    # Update
    response = client.put(
        f"/tasks/{task_id}",
        json={"title": "Updated", "status": "completed"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["status"] == "completed"

def test_update_task_not_found():
    """PUT /tasks/{id} returns 404 for missing task."""
    response = client.put(
        "/tasks/99999",
        json={"title": "Updated"}
    )
    assert response.status_code == 404

def test_delete_task():
    """DELETE /tasks/{id} deletes a task."""
    # Create first
    create_response = client.post("/tasks", json={"title": "To delete"})
    task_id = create_response.json()["id"]

    # Delete
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 200

    # Verify deleted
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404

def test_delete_task_not_found():
    """DELETE /tasks/{id} returns 404 for missing task."""
    response = client.delete("/tasks/99999")
    assert response.status_code == 404
```

## Testing Error Handling

### Testing HTTPException Responses

```python
def test_get_task_not_found():
    """GET /tasks/{id} returns 404 for missing task."""
    response = client.get("/tasks/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_create_task_empty_title():
    """POST /tasks with empty title returns 400."""
    response = client.post(
        "/tasks",
        json={"title": "   "}  # Whitespace only
    )
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"].lower()

def test_update_task_invalid_status():
    """PUT /tasks/{id} with invalid status returns 400."""
    # Create task first
    create_response = client.post("/tasks", json={"title": "Test"})
    task_id = create_response.json()["id"]

    # Try invalid status
    response = client.put(
        f"/tasks/{task_id}",
        json={"title": "Test", "status": "invalid"}
    )
    assert response.status_code == 400
    assert "invalid status" in response.json()["detail"].lower()
```

### Testing Status Codes

```python
def test_create_returns_201():
    """POST /tasks returns 201 Created."""
    response = client.post("/tasks", json={"title": "Test"})
    assert response.status_code == 201

def test_delete_returns_200_or_204():
    """DELETE /tasks/{id} returns appropriate status."""
    create_response = client.post("/tasks", json={"title": "Test"})
    task_id = create_response.json()["id"]

    delete_response = client.delete(f"/tasks/{task_id}")
    assert delete_response.status_code in [200, 204]
```

### Testing Error Message Quality

```python
def test_error_message_includes_context():
    """Error messages should include helpful context."""
    response = client.get("/tasks/999")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "999" in detail  # Includes the task ID
    assert "not found" in detail.lower()

def test_error_message_includes_valid_options():
    """Error messages should suggest valid options."""
    # Create task first
    create_response = client.post("/tasks", json={"title": "Test"})
    task_id = create_response.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        json={"title": "Test", "status": "invalid"}
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "pending" in detail  # Mentions valid options
    assert "completed" in detail
```

### Testing 400 vs 422 Distinction

```python
def test_422_schema_validation():
    """POST /tasks without required field returns 422."""
    response = client.post(
        "/tasks",
        json={"description": "Missing title"}  # title is required
    )
    assert response.status_code == 422
    # Pydantic validation error format
    assert "detail" in response.json()

def test_400_business_rule():
    """POST /tasks with invalid business logic returns 400."""
    response = client.post(
        "/tasks",
        json={"title": "   "}  # Title exists but empty whitespace
    )
    assert response.status_code == 400
    assert "whitespace" in response.json()["detail"].lower()

def test_422_type_validation():
    """POST /tasks with wrong type returns 422."""
    response = client.post(
        "/tasks",
        json={"title": 123}  # Should be string
    )
    assert response.status_code == 422
```

## Testing Authentication

### Testing Protected Endpoints

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.testclient import TestClient

app = FastAPI()
security = HTTPBearer()

@app.get("/protected")
async def protected_route(token: str = Depends(security)):
    return {"message": "Access granted"}

client = TestClient(app)

def test_protected_without_auth():
    response = client.get("/protected")
    assert response.status_code == 403

def test_protected_with_auth():
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer fake-token"}
    )
    assert response.status_code == 200
```

### Testing OAuth2 Login

```python
def test_login():
    response = client.post(
        "/token",
        data={
            "username": "johndoe",
            "password": "secret"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_invalid_credentials():
    response = client.post(
        "/token",
        data={
            "username": "wrong",
            "password": "wrong"
        }
    )
    assert response.status_code == 401
```

### Testing with Valid Token

```python
def test_read_current_user():
    # First, get a token
    login_response = client.post(
        "/token",
        data={"username": "johndoe", "password": "secret"}
    )
    token = login_response.json()["access_token"]

    # Then use it
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "johndoe"
```

## Testing Dependencies

### Overriding Dependencies for Testing

The power of dependency injection is testability. Override any dependency with a mock:

```python
from fastapi.testclient import TestClient
from main import app, get_config

def override_get_config():
    return {"app_name": "Test API", "version": "test"}

app.dependency_overrides[get_config] = override_get_config

client = TestClient(app)

def test_with_mock_config():
    response = client.get("/tasks")
    assert response.json()["app"] == "Test API"
```

**Clean up after tests:**

```python
import pytest

@pytest.fixture
def client():
    # Setup: override dependency
    app.dependency_overrides[get_config] = override_get_config
    yield TestClient(app)
    # Teardown: clear overrides
    app.dependency_overrides.clear()

def test_with_config_override(client):
    response = client.get("/tasks")
    assert response.json()["app"] == "Test API"
```

### Testing Yield Dependencies

Dependencies with `yield` can be tested too:

```python
def get_db():
    db = create_test_db()
    yield db
    db.close()

def override_get_db():
    db = create_mock_db()
    yield db
    # Cleanup still happens

app.dependency_overrides[get_db] = override_get_db
```

### Complete Example: Testing with Database Mock

```python
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

async def get_db():
    # Real database connection
    return {"db": "real"}

@app.get("/items/")
async def read_items(db: dict = Depends(get_db)):
    return {"db": db}

# Test with mock database
def override_get_db():
    return {"db": "test"}

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_read_items():
    response = client.get("/items/")
    assert response.json() == {"db": {"db": "test"}}
```

### Fixture for Dependency Override

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_db

@pytest.fixture
def test_db():
    # Setup test database
    return {"db": "test"}

@pytest.fixture
def client(test_db):
    def override_get_db():
        return test_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_read_items(client):
    response = client.get("/items/")
    assert response.status_code == 200
```

## Testing File Uploads

### Single File Upload

```python
def test_upload_file():
    files = {"file": ("test.txt", b"file content", "text/plain")}
    response = client.post("/upload/", files=files)
    assert response.status_code == 200
    assert response.json()["filename"] == "test.txt"
```

### Multiple File Uploads

```python
def test_upload_multiple_files():
    files = [
        ("files", ("test1.txt", b"content 1", "text/plain")),
        ("files", ("test2.txt", b"content 2", "text/plain")),
    ]
    response = client.post("/uploadfiles/", files=files)
    assert response.status_code == 200
    assert len(response.json()["filenames"]) == 2
```

### File Upload with Form Data

```python
def test_upload_with_form():
    files = {"file": ("test.txt", b"content", "text/plain")}
    data = {"description": "Test file"}
    response = client.post("/upload/", files=files, data=data)
    assert response.status_code == 200
```

## Testing Error Cases

### Testing 404 Errors

```python
def test_read_nonexistent_item():
    response = client.get("/items/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}
```

### Testing Validation Errors

```python
def test_create_item_invalid_data():
    response = client.post(
        "/items/",
        json={"name": "Test"}  # Missing required "price"
    )
    assert response.status_code == 422  # Unprocessable Entity
    assert "detail" in response.json()
```

### Testing Duplicate Items

```python
def test_create_duplicate_item():
    # Create first item
    client.post("/items/", json={"id": "foo", "name": "Foo"})

    # Try to create duplicate
    response = client.post("/items/", json={"id": "foo", "name": "Foo"})
    assert response.status_code == 409
    assert response.json() == {"detail": "Item already exists"}
```

## Test Organization Patterns

### Using pytest Fixtures

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_item():
    return {"name": "Test Item", "price": 10.5}

def test_create_item(client, sample_item):
    response = client.post("/items/", json=sample_item)
    assert response.status_code == 201
```

### Setup and Teardown

```python
import pytest

@pytest.fixture(scope="function")
def test_data():
    # Setup: Create test data
    data = {"test": "data"}
    yield data
    # Teardown: Clean up
    # data.clear()

def test_with_setup(test_data):
    assert test_data["test"] == "data"
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("item_id,expected", [
    (1, 200),
    (2, 200),
    (999, 404),
])
def test_get_item(client, item_id, expected):
    response = client.get(f"/items/{item_id}")
    assert response.status_code == expected
```

### Test Classes

```python
class TestItems:
    def test_create_item(self, client):
        response = client.post("/items/", json={"name": "Test"})
        assert response.status_code == 201

    def test_read_items(self, client):
        response = client.get("/items/")
        assert response.status_code == 200

    def test_update_item(self, client):
        response = client.put("/items/1", json={"name": "Updated"})
        assert response.status_code == 200
```

## Async Tests

For async operations outside TestClient:

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_async_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
```

## Complete Testing Example

**app/main.py:**
```python
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Annotated

app = FastAPI()

fake_db = {}

class Item(BaseModel):
    name: str
    price: float

@app.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: str, x_token: Annotated[str, Header()]):
    if x_token != "secret-token":
        raise HTTPException(status_code=400, detail="Invalid X-Token")
    if item_id not in fake_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return fake_db[item_id]

@app.post("/items/", response_model=Item, status_code=201)
async def create_item(item: Item, x_token: Annotated[str, Header()]):
    if x_token != "secret-token":
        raise HTTPException(status_code=400, detail="Invalid X-Token")
    if item.name in fake_db:
        raise HTTPException(status_code=409, detail="Item exists")
    fake_db[item.name] = item
    return item
```

**tests/test_main.py:**
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app, fake_db

@pytest.fixture
def client():
    fake_db.clear()  # Clean database before each test
    return TestClient(app)

@pytest.fixture
def auth_headers():
    return {"X-Token": "secret-token"}

def test_read_item(client, auth_headers):
    # Create item first
    client.post(
        "/items/",
        headers=auth_headers,
        json={"name": "foo", "price": 10.5}
    )

    # Read item
    response = client.get("/items/foo", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"name": "foo", "price": 10.5}

def test_read_item_bad_token(client):
    response = client.get("/items/foo", headers={"X-Token": "wrong"})
    assert response.status_code == 400

def test_read_nonexistent_item(client, auth_headers):
    response = client.get("/items/nonexistent", headers=auth_headers)
    assert response.status_code == 404

def test_create_item(client, auth_headers):
    response = client.post(
        "/items/",
        headers=auth_headers,
        json={"name": "test", "price": 99.9}
    )
    assert response.status_code == 201
    assert response.json() == {"name": "test", "price": 99.9}

def test_create_duplicate_item(client, auth_headers):
    item_data = {"name": "duplicate", "price": 10.0}

    # Create first time
    client.post("/items/", headers=auth_headers, json=item_data)

    # Try to create again
    response = client.post("/items/", headers=auth_headers, json=item_data)
    assert response.status_code == 409
```

## Running Tests

Always use `uv run` to execute tests with the correct virtual environment:

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_main.py

# Run specific test
uv run pytest tests/test_main.py::test_read_main

# Run with verbose output
uv run pytest -v

# Run tests matching a pattern
uv run pytest -k "test_create" -v

# Run with coverage
uv run pytest --cov=app tests/ --cov-report=html

# Run with coverage and missing lines
uv run pytest --cov=app --cov-report=term-missing tests/
```

---

## Agent-Specific Testing Considerations

When building FastAPI applications for AI agents, special testing considerations apply:

### Test Contract Stability

Agents depend on stable API contracts. Test that:

```python
def test_response_schema_stability():
    """Ensure response schema remains stable for agents."""
    response = client.get("/tasks/1")
    data = response.json()

    # Agent expects these exact fields
    assert "id" in data
    assert "title" in data
    assert "status" in data
    assert "created_at" in data

    # Verify types (agents can't handle type changes)
    assert isinstance(data["id"], int)
    assert isinstance(data["title"], str)
    assert isinstance(data["status"], str)
```

### Test Error Response Consistency

Agents need consistent error formats:

```python
def test_error_format_consistency():
    """All errors should have consistent format."""
    # Test 404
    response = client.get("/tasks/99999")
    assert response.status_code == 404
    assert "detail" in response.json()

    # Test 422 (validation error)
    response = client.post("/tasks", json={"invalid": "data"})
    assert response.status_code == 422
    assert "detail" in response.json()

    # Test 500 (simulate server error)
    response = client.get("/tasks/error")
    assert response.status_code == 500
    assert "detail" in response.json()
```

### Test Idempotency

Many agent operations should be idempotent:

```python
def test_create_idempotency():
    """Creating same resource twice should be handled gracefully."""
    task_data = {"title": "Unique Task", "idempotency_key": "abc123"}

    # First creation
    response1 = client.post("/tasks", json=task_data)
    assert response1.status_code == 201
    task_id = response1.json()["id"]

    # Second creation with same idempotency key
    response2 = client.post("/tasks", json=task_data)
    assert response2.status_code == 200  # Not 201
    assert response2.json()["id"] == task_id  # Same task returned
```

### Test Rate Limiting

Agents can make rapid API calls:

```python
def test_rate_limiting():
    """API should handle rapid requests gracefully."""
    for i in range(100):
        response = client.get(f"/tasks/{i}")
        assert response.status_code in [200, 404, 429]  # 429 = Too Many Requests

    # If rate limited, error should be clear
    if response.status_code == 429:
        assert "rate limit" in response.json()["detail"].lower()
```

### Test Pagination Consistency

Agents often paginate through results:

```python
def test_pagination_consistency():
    """Pagination should be stable across requests."""
    # First page
    response1 = client.get("/tasks?limit=10&offset=0")
    assert response1.status_code == 200
    assert len(response1.json()["items"]) <= 10

    # Second page should not overlap
    response2 = client.get("/tasks?limit=10&offset=10")
    assert response2.status_code == 200

    # No items should appear in both pages
    items1 = {item["id"] for item in response1.json()["items"]}
    items2 = {item["id"] for item in response2.json()["items"]}
    assert items1.isdisjoint(items2)
```

### Test Versioning

Agents need API version stability:

```python
def test_api_version_header():
    """API version should be exposed in headers."""
    response = client.get("/")
    assert "X-API-Version" in response.headers
    assert response.headers["X-API-Version"] == "1.0.0"

def test_deprecated_endpoint_warning():
    """Deprecated endpoints should warn but still work."""
    response = client.get("/old-endpoint")
    assert response.status_code == 200
    assert "X-Deprecated" in response.headers
    assert "sunset-date" in response.headers["X-Deprecated"].lower()
```

---

## Common Mistakes and Solutions

### Mistake 1: Testing Implementation Instead of Behavior

**❌ Wrong:**
```python
def test_get_user_calls_database():
    """Bad: Testing internal implementation."""
    response = client.get("/users/1")
    assert mock_db.query.called  # Testing internal detail
```

**✅ Correct:**
```python
def test_get_user_returns_correct_data():
    """Good: Testing observable behavior."""
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert "name" in response.json()
```

### Mistake 2: Tests That Pass for Wrong Reasons

**❌ Wrong:**
```python
def test_create_task():
    """Bad: Not checking actual response data."""
    response = client.post("/tasks", json={"title": "Test"})
    assert response.status_code == 201  # Could return anything!
```

**✅ Correct:**
```python
def test_create_task():
    """Good: Verify complete response."""
    response = client.post("/tasks", json={"title": "Test"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test"
    assert data["status"] == "pending"
    assert "id" in data
```

### Mistake 3: Brittle Tests (Too Specific)

**❌ Wrong:**
```python
def test_list_tasks():
    """Bad: Expects exact database state."""
    response = client.get("/tasks")
    assert len(response.json()) == 5  # Breaks if data changes
```

**✅ Correct:**
```python
def test_list_tasks():
    """Good: Tests structure, not specific state."""
    response = client.get("/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    if len(response.json()) > 0:
        assert "id" in response.json()[0]
        assert "title" in response.json()[0]
```

### Mistake 4: Not Testing Error Cases

**❌ Wrong:**
```python
def test_endpoints():
    """Bad: Only tests happy path."""
    assert client.get("/tasks").status_code == 200
    assert client.post("/tasks", json={...}).status_code == 201
```

**✅ Correct:**
```python
def test_task_not_found():
    """Good: Tests error handling."""
    response = client.get("/tasks/99999")
    assert response.status_code == 404

def test_invalid_task_data():
    """Good: Tests validation."""
    response = client.post("/tasks", json={"title": ""})
    assert response.status_code == 422
```

### Mistake 5: Forgetting to Use `uv run`

**❌ Wrong:**
```bash
pytest tests/  # Uses system Python, wrong dependencies
```

**✅ Correct:**
```bash
uv run pytest tests/  # Uses project virtual environment
```

---

## Key Points

- **Write tests manually first** - Understand testing before using AI to generate tests
- **Test for agents** - Agent APIs need stable contracts and consistent errors
- **Use TDD (Red-Green-Refactor)** - Design interfaces before implementation
- **Use `uv run`** - Always run tests with the correct virtual environment
- Use `TestClient` from `fastapi.testclient`
- Write regular `def` functions, not `async def`
- Don't use `await` with TestClient
- Override dependencies for testing
- Use pytest fixtures for setup/teardown
- Test success cases AND error cases
- Use parametrized tests for multiple scenarios
- Clean test data between tests
- TestClient handles application lifecycle automatically
- Test behavior, not implementation
- Keep tests focused and maintainable

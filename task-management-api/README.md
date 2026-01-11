# Task Management API

A production-ready Task Management API built with FastAPI, SQLModel, and pytest following Test-Driven Development (TDD) principles.

## Features

- ✅ Full CRUD operations for tasks
- ✅ Database persistence with SQLModel
- ✅ Input validation with Pydantic
- ✅ Comprehensive test coverage (98%)
- ✅ Type hints on all parameters
- ✅ Automatic API documentation (Swagger UI)
- ✅ CORS middleware for cross-origin requests
- ✅ Production-ready with lifespan events
- ✅ Test-Driven Development approach

## Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLModel** - ORM combining Pydantic and SQLAlchemy
- **pytest** - Testing framework
- **uv** - Fast Python package manager

## Project Structure

```
task-management-api/
├── config.py           # Application configuration
├── database.py         # Database connection and session
├── models.py           # SQLModel models and Pydantic schemas
├── main.py             # FastAPI application and endpoints
├── tests/              # Test suite
│   ├── conftest.py     # Pytest fixtures
│   └── test_tasks.py   # Comprehensive endpoint tests
├── .env                # Environment variables (not committed)
├── .env.example        # Environment template
├── .gitignore          # Git ignore rules
└── pyproject.toml      # Project dependencies
```

## Setup and Installation

### Prerequisites

- Python 3.11 or higher
- uv package manager ([install from https://docs.astral.sh/uv/](https://docs.astral.sh/uv/))

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd task-management-api
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` if needed (default uses SQLite):
   ```env
   DATABASE_URL=sqlite:///./tasks.db
   ENVIRONMENT=development
   ```

4. **Run the application**
   ```bash
   uv run uvicorn main:app --reload
   ```

   The API will be available at `http://localhost:8000`

## API Endpoints

### Root Endpoint

**GET /**
- Returns API information and health check
- Response:
  ```json
  {
    "message": "Task Management API",
    "version": "1.0.0",
    "status": "operational"
  }
  ```

### Task Endpoints

#### Create Task
**POST /tasks**

Request body:
```json
{
  "title": "Complete project",
  "description": "Finish the API implementation"
}
```

Response (201 Created):
```json
{
  "id": 1,
  "title": "Complete project",
  "description": "Finish the API implementation",
  "status": "pending",
  "created_at": "2024-01-11T10:00:00Z",
  "updated_at": "2024-01-11T10:00:00Z"
}
```

#### List Tasks
**GET /tasks**

Optional query parameters:
- `status_filter` - Filter by status (pending, in_progress, completed)

Example: `GET /tasks?status_filter=pending`

Response (200 OK):
```json
[
  {
    "id": 1,
    "title": "Complete project",
    "description": "Finish the API implementation",
    "status": "pending",
    "created_at": "2024-01-11T10:00:00Z",
    "updated_at": "2024-01-11T10:00:00Z"
  }
]
```

#### Get Single Task
**GET /tasks/{task_id}**

Response (200 OK):
```json
{
  "id": 1,
  "title": "Complete project",
  "description": "Finish the API implementation",
  "status": "pending",
  "created_at": "2024-01-11T10:00:00Z",
  "updated_at": "2024-01-11T10:00:00Z"
}
```

#### Update Task
**PUT /tasks/{task_id}**

Request body (all fields optional):
```json
{
  "title": "Updated title",
  "description": "Updated description",
  "status": "completed"
}
```

Valid status values: `pending`, `in_progress`, `completed`

Response (200 OK): Updated task object

#### Delete Task
**DELETE /tasks/{task_id}**

Response (204 No Content)

## Testing

The project includes comprehensive tests with 98% code coverage.

### Run Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=. --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_tasks.py

# Run specific test class
uv run pytest tests/test_tasks.py::TestCreateTask

# Run specific test
uv run pytest tests/test_tasks.py::TestCreateTask::test_create_task_with_title_only
```

### Test Coverage

Current coverage: **98%**

Test categories:
- ✅ Root endpoint (1 test)
- ✅ Create task (5 tests)
- ✅ List tasks (6 tests)
- ✅ Get single task (2 tests)
- ✅ Update task (7 tests)
- ✅ Delete task (3 tests)
- ✅ Complete workflow (2 tests)

**Total: 26 tests**

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Usage Examples

### Using curl

```bash
# Create a task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn FastAPI", "description": "Complete the tutorial"}'

# List all tasks
curl http://localhost:8000/tasks

# Filter tasks by status
curl http://localhost:8000/tasks?status_filter=pending

# Get a specific task
curl http://localhost:8000/tasks/1

# Update a task
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'

# Delete a task
curl -X DELETE http://localhost:8000/tasks/1
```

### Using Python requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Create a task
response = requests.post(
    f"{BASE_URL}/tasks",
    json={"title": "Learn FastAPI", "description": "Complete the tutorial"}
)
task = response.json()
print(f"Created task: {task['id']}")

# List tasks
response = requests.get(f"{BASE_URL}/tasks")
tasks = response.json()
print(f"Total tasks: {len(tasks)}")

# Update task
response = requests.put(
    f"{BASE_URL}/tasks/{task['id']}",
    json={"status": "completed"}
)
updated_task = response.json()
print(f"Updated task status: {updated_task['status']}")
```

## Database Configuration

The API supports multiple database backends through SQLModel:

### SQLite (Default)
```env
DATABASE_URL=sqlite:///./tasks.db
```

### PostgreSQL
```env
DATABASE_URL=postgresql://user:password@localhost/taskdb
```

### PostgreSQL with Neon
```env
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require
```

## Production Deployment

### Using uvicorn

```bash
# Development
uv run uvicorn main:app --reload

# Production
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY . .

# Install dependencies
RUN uv sync

# Run the application
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t task-api .
docker run -p 8000:8000 task-api
```

## Development

### Code Style

The project follows:
- Type hints on all function parameters
- Descriptive function names
- Dictionary returns (never None)
- Pydantic for validation
- SQLModel for ORM

### Adding New Features

1. **Write tests first** (TDD approach)
   ```python
   # tests/test_tasks.py
   def test_new_feature(client):
       # Test implementation
       assert expected == actual
   ```

2. **Run tests (they should fail - RED)**
   ```bash
   uv run pytest tests/test_tasks.py::test_new_feature
   ```

3. **Implement feature**
   ```python
   # main.py
   @app.get("/new-feature")
   async def new_feature():
       return {"result": "implemented"}
   ```

4. **Run tests again (they should pass - GREEN)**
   ```bash
   uv run pytest
   ```

5. **Refactor if needed**

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK` - Successful GET, PUT
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid input (e.g., invalid status)
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error

Error response format:
```json
{
  "detail": "Task with ID 999 not found"
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./tasks.db` |
| `ENVIRONMENT` | Environment (development/production) | `development` |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Implement your changes
5. Run tests and ensure they pass
6. Submit a pull request

## License

MIT License

## Support

For issues and questions:
- Open an issue on GitHub
- Check the API documentation at `/docs`

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [pytest](https://docs.pytest.org/)
- [uv](https://docs.astral.sh/uv/)

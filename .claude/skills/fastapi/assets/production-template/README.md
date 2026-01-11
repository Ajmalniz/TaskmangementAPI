# FastAPI Production Template

A production-ready FastAPI application template with best practices, testing, and Docker support.

## Features

- ✅ Structured application layout
- ✅ Configuration management with Pydantic Settings
- ✅ CORS and GZip middleware
- ✅ API routers for modular organization
- ✅ Pydantic schemas for validation
- ✅ Comprehensive test suite with pytest
- ✅ Docker and docker-compose support
- ✅ Environment-based configuration
- ✅ Health check endpoint

## Project Structure

```
production-template/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── config.py            # Settings and configuration
│   ├── routers/             # API route handlers
│   │   └── items.py
│   ├── schemas/             # Pydantic models
│   │   └── item.py
│   ├── models/              # Database models (if using ORM)
│   ├── services/            # Business logic
│   └── dependencies/        # Dependency injection
├── tests/                   # Test files
│   ├── test_main.py
│   └── test_items.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── pytest.ini
└── README.md
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Run the Application

#### Development Mode
```bash
fastapi dev app/main.py
```

Or with uvicorn:
```bash
uvicorn app.main:app --reload
```

#### Production Mode
```bash
fastapi run app/main.py --port 8000 --workers 4
```

Or with Gunicorn:
```bash
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app tests/
```

## Docker Deployment

### Build and Run

```bash
# Build image
docker build -t fastapi-production .

# Run container
docker run -d -p 8000:80 --name fastapi fastapi-production
```

### Using Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs (dev only)
- ReDoc: http://localhost:8000/redoc (dev only)
- OpenAPI Schema: http://localhost:8000/openapi.json

## API Endpoints

### Core
- `GET /` - Welcome message
- `GET /health` - Health check

### Items (API v1)
- `GET /api/v1/items` - List all items
- `GET /api/v1/items/{id}` - Get item by ID
- `POST /api/v1/items` - Create new item
- `PUT /api/v1/items/{id}` - Update item
- `DELETE /api/v1/items/{id}` - Delete item

## Configuration

Configuration is managed through environment variables and the `.env` file. Key settings:

- `APP_NAME` - Application name
- `DEBUG` - Debug mode (disable in production)
- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - Secret key for JWT tokens
- `CORS_ORIGINS` - Allowed CORS origins

See `.env.example` for all available settings.

## Adding New Features

### Add a New Router

1. Create router file in `app/routers/`:
```python
# app/routers/users.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
async def get_users():
    return []
```

2. Include in `app/main.py`:
```python
from app.routers import users
app.include_router(users.router, prefix="/api/v1", tags=["users"])
```

### Add a New Schema

Create Pydantic models in `app/schemas/`:
```python
# app/schemas/user.py
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    email: str
```

## Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure proper `CORS_ORIGINS`
- [ ] Enable HTTPS
- [ ] Set up database connection pooling
- [ ] Configure logging
- [ ] Implement rate limiting
- [ ] Add authentication/authorization
- [ ] Set up monitoring
- [ ] Configure automated backups

## License

MIT

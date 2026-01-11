# Production Deployment Reference

Complete guide to deploying FastAPI applications in production with Uvicorn, Docker, and best practices.

## Table of Contents
- Production Server (Uvicorn)
- Server Workers and Process Managers
- Docker Deployment
- Environment Configuration
- HTTPS and Security
- Performance Optimization
- Monitoring and Logging

## Production Server (Uvicorn)

### Basic Production Command

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### With Workers (Multi-process)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Workers calculation:**
```
workers = (2 × CPU cores) + 1
```

For a 4-core machine: `--workers 9`

### Using Gunicorn with Uvicorn Workers

Gunicorn acts as the process manager:

```bash
pip install gunicorn
```

```bash
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
```

### FastAPI CLI (Recommended)

```bash
# Development
fastapi dev app/main.py

# Production
fastapi run app/main.py --port 8000 --workers 4
```

## Server Configuration

### Uvicorn Configuration File

**uvicorn_config.py:**
```python
from uvicorn.config import Config

config = Config(
    app="app.main:app",
    host="0.0.0.0",
    port=8000,
    workers=4,
    log_level="info",
    access_log=True,
    use_colors=False,
    reload=False,  # Never True in production
)
```

Run with:
```bash
uvicorn --config uvicorn_config.py
```

### Gunicorn Configuration File

**gunicorn_config.py:**
```python
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "fastapi"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Server hooks
def on_starting(server):
    print("Starting Gunicorn")

def on_reload(server):
    print("Reloading Gunicorn")

def when_ready(server):
    print("Gunicorn is ready")

def on_exit(server):
    print("Exiting Gunicorn")
```

Run with:
```bash
gunicorn -c gunicorn_config.py app.main:app
```

## Docker Deployment

### Basic Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /code

# Install dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy application
COPY ./app /code/app

# Run the application
CMD ["fastapi", "run", "app/main.py", "--port", "80"]
```

### Multi-stage Dockerfile (Optimized)

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /code

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /code

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY ./app /code/app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /code
USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:80/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
```

### Production Dockerfile with Gunicorn

```dockerfile
FROM python:3.11-slim

WORKDIR /code

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application
COPY ./app /code/app

# Run with Gunicorn
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:80"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:80"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/dbname
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
    restart: unless-stopped
    volumes:
      - ./app:/code/app

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=dbname
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

### Build and Run

```bash
# Build image
docker build -t my-fastapi-app .

# Run container
docker run -d -p 8000:80 --name fastapi my-fastapi-app

# Using docker-compose
docker-compose up -d
```

## Environment Configuration

### Using .env Files

**.env:**
```env
# Application
APP_NAME=MyAPI
DEBUG=False
VERSION=1.0.0

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External Services
REDIS_URL=redis://localhost:6379
EMAIL_SERVICE_API_KEY=your-api-key
```

### Settings with Pydantic

**app/config.py:**
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "FastAPI App"
    debug: bool = False
    version: str = "1.0.0"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Database
    database_url: str

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()
```

**Usage:**
```python
from fastapi import Depends
from app.config import get_settings, Settings

@app.get("/info")
async def info(settings: Settings = Depends(get_settings)):
    return {
        "app_name": settings.app_name,
        "version": settings.version
    }
```

## HTTPS and Security

### Nginx Reverse Proxy

**nginx.conf:**
```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Traefik Configuration

**docker-compose.yml with Traefik:**
```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.myresolver.acme.tlschallenge=true"
      - "--certificatesresolvers.myresolver.acme.email=admin@example.com"
      - "--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"

  web:
    build: .
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=Host(`example.com`)"
      - "traefik.http.routers.web.entrypoints=websecure"
      - "traefik.http.routers.web.tls.certresolver=myresolver"
```

## Performance Optimization

### Enable Gzip Compression

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Connection Pooling

**For PostgreSQL:**
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

### Caching with Redis

```python
from redis import asyncio as aioredis
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
async def startup():
    app.state.redis = await aioredis.from_url("redis://localhost")

@app.on_event("shutdown")
async def shutdown():
    await app.state.redis.close()

@app.get("/items/{item_id}")
async def get_item(item_id: int, request: Request):
    # Try cache first
    cached = await request.app.state.redis.get(f"item:{item_id}")
    if cached:
        return json.loads(cached)

    # Fetch from database
    item = fetch_item(item_id)

    # Cache result
    await request.app.state.redis.setex(
        f"item:{item_id}",
        3600,  # 1 hour
        json.dumps(item)
    )
    return item
```

## Monitoring and Logging

### Structured Logging

```python
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

logger = setup_logging()

@app.get("/items/")
async def read_items():
    logger.info("Reading items", extra={"user_id": 123})
    return items
```

### Health Check Endpoint

```python
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/health/detailed")
async def detailed_health():
    # Check database
    db_healthy = await check_database()

    # Check Redis
    redis_healthy = await check_redis()

    if db_healthy and redis_healthy:
        return {
            "status": "healthy",
            "database": "ok",
            "redis": "ok"
        }
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "ok" if db_healthy else "error",
                "redis": "ok" if redis_healthy else "error"
            }
        )
```

### Application Metrics (Prometheus)

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

Instrumentator().instrument(app).expose(app)

# Metrics available at /metrics
```

## Systemd Service

**fastapi.service:**
```ini
[Unit]
Description=FastAPI Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/myapp
Environment="PATH=/opt/myapp/venv/bin"
ExecStart=/opt/myapp/venv/bin/gunicorn \
    -c /opt/myapp/gunicorn_config.py \
    app.main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable fastapi
sudo systemctl start fastapi
sudo systemctl status fastapi
```

## Deployment Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY`
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS/TLS
- [ ] Set up database connection pooling
- [ ] Configure proper logging
- [ ] Implement health checks
- [ ] Set up monitoring (metrics, logs)
- [ ] Configure proper number of workers
- [ ] Use environment variables for secrets
- [ ] Set up automated backups
- [ ] Configure rate limiting
- [ ] Add security headers
- [ ] Test deployment in staging first
- [ ] Set up CI/CD pipeline
- [ ] Document deployment process

## Key Points

- Use Uvicorn with Gunicorn for production
- Calculate workers: `(2 × CPU) + 1`
- Use multi-stage Docker builds for smaller images
- Store secrets in environment variables, not code
- Use Nginx or Traefik for reverse proxy and HTTPS
- Enable gzip compression for large responses
- Implement health checks for monitoring
- Use connection pooling for databases
- Structure logs for easy parsing
- Never set `reload=True` in production
- Run as non-root user in containers
- Use systemd or Docker for process management

---
name: docker-compose-gen
description: Generate production-ready docker-compose.yml files for Python FastAPI applications with database services (PostgreSQL, MySQL, SQLite), Redis, and proper networking. Use when the user wants to containerize their application, needs Docker setup for development or production, wants to add database services to their Docker setup, or asks about Docker Compose configuration for FastAPI projects.
---

# Docker Compose Generator

Generate production-ready `docker-compose.yml` files for FastAPI applications with complete service orchestration.

## What This Skill Does

This skill automatically generates Docker Compose configurations that include:
- FastAPI application container with proper build configuration
- Database services (PostgreSQL, MySQL, or MongoDB)
- Optional Redis for caching
- Proper networking between services
- Volume management for data persistence
- Environment variable configuration
- Health checks for all services

## When to Use

Use this skill when the user:
- Wants to containerize their FastAPI application
- Needs to set up a development environment with Docker
- Wants to add database services to their Docker setup
- Asks about deploying with Docker Compose
- Needs a multi-service setup (API + Database + Cache)

## How to Use

### Step 1: Gather Requirements

Ask the user (if not already specified):
1. **Database type**: PostgreSQL (recommended), MySQL, MongoDB, or None
2. **Cache layer**: Include Redis? (yes/no)
3. **Environment**: Development or Production
4. **Additional services**: Any other services needed?

### Step 2: Analyze Project Structure

Check the current project for:
- Python version (from `.python-version` or `pyproject.toml`)
- Dependencies (from `pyproject.toml` or `requirements.txt`)
- Entry point (typically `main.py` or `app.py`)
- Environment variables (from `.env.example`)

### Step 3: Generate Configuration Files

Create the following files in order:

#### 1. Dockerfile

Generate a multi-stage Dockerfile optimized for Python FastAPI:

```dockerfile
# Multi-stage build for smaller image size
FROM python:3.11-slim as builder

WORKDIR /app

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Adjust based on project specifics:
- Python version from project
- Entry point module name
- Port number if different
- Add `--reload` flag for development

#### 2. docker-compose.yml

Generate based on user requirements. See `references/compose-templates.md` for complete templates.

**Basic structure:**
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app
    restart: unless-stopped

  db:
    # Database configuration based on user choice
    # See compose-templates.md for specifics

volumes:
  postgres_data:  # or mysql_data, mongo_data

networks:
  app_network:
    driver: bridge
```

#### 3. .dockerignore

Generate to exclude unnecessary files:

```
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
.coverage
.env
.git/
.gitignore
*.md
!README.md
.vscode/
.idea/
*.db
*.sqlite
```

#### 4. Environment Configuration

Update `.env.example` with Docker-specific variables:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@db:5432/dbname

# Application Configuration
ENVIRONMENT=development
DEBUG=true

# Redis (if included)
REDIS_URL=redis://redis:6379/0
```

### Step 4: Generate Usage Instructions

After creating files, provide clear instructions:

1. **Build and start services:**
   ```bash
   docker-compose up -d --build
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f api
   ```

3. **Stop services:**
   ```bash
   docker-compose down
   ```

4. **Stop and remove volumes:**
   ```bash
   docker-compose down -v
   ```

5. **Access the API:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

6. **Run database migrations (if applicable):**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

## Templates and References

For complete docker-compose templates with different database options, see `references/compose-templates.md`.

## Production Considerations

When generating for production, include:
- Resource limits (CPU, memory)
- Restart policies
- Logging configuration
- Secret management (Docker secrets)
- Network security
- Volume backup strategies
- Health check endpoints

Example production additions:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Troubleshooting

Common issues to address:

1. **Port conflicts**: Check if ports 8000, 5432, 3306, or 6379 are already in use
2. **Permission issues**: Ensure proper file permissions for volumes
3. **Database connection**: Verify `DATABASE_URL` uses service name (e.g., `db`, not `localhost`)
4. **Build failures**: Check Dockerfile syntax and dependency availability

## Output Format

Always create these files in order:
1. `Dockerfile` - Application containerization
2. `docker-compose.yml` - Service orchestration
3. `.dockerignore` - Build optimization
4. Update `.env.example` - Configuration template
5. Provide usage instructions

Confirm with user before writing files if any requirements are unclear.

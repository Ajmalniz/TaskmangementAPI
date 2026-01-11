# Docker Compose Templates

Complete docker-compose.yml templates for different database configurations.

## Table of Contents

- [PostgreSQL Configuration](#postgresql-configuration)
- [MySQL Configuration](#mysql-configuration)
- [MongoDB Configuration](#mongodb-configuration)
- [With Redis Cache](#with-redis-cache)
- [Development vs Production](#development-vs-production)

---

## PostgreSQL Configuration

Most common setup for FastAPI applications.

```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: fastapi_app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/appdb
      - ENVIRONMENT=development
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app
    networks:
      - app_network
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    container_name: postgres_db
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=appdb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  app_network:
    driver: bridge
```

---

## MySQL Configuration

Alternative to PostgreSQL.

```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: fastapi_app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql://root:rootpassword@db:3306/appdb
      - ENVIRONMENT=development
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app
    networks:
      - app_network
    restart: unless-stopped

  db:
    image: mysql:8.0
    container_name: mysql_db
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=appdb
      - MYSQL_USER=appuser
      - MYSQL_PASSWORD=apppassword
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - app_network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-prootpassword"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  mysql_data:

networks:
  app_network:
    driver: bridge
```

---

## MongoDB Configuration

For NoSQL database requirements.

```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: fastapi_app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mongodb://root:rootpassword@db:27017/appdb?authSource=admin
      - ENVIRONMENT=development
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app
    networks:
      - app_network
    restart: unless-stopped

  db:
    image: mongo:6
    container_name: mongo_db
    environment:
      - MONGO_INITDB_ROOT_USERNAME=root
      - MONGO_INITDB_ROOT_PASSWORD=rootpassword
      - MONGO_INITDB_DATABASE=appdb
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    networks:
      - app_network
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  mongo_data:

networks:
  app_network:
    driver: bridge
```

---

## With Redis Cache

Add Redis for caching layer.

```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: fastapi_app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/appdb
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=development
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - .:/app
    networks:
      - app_network
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    container_name: postgres_db
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=appdb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: redis_cache
    ports:
      - "6379:6379"
    networks:
      - app_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  app_network:
    driver: bridge
```

---

## Development vs Production

### Development Configuration

Development setup with hot reload and debugging:

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: fastapi_dev
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/appdb
      - ENVIRONMENT=development
      - DEBUG=true
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app  # Mount code for hot reload
    networks:
      - app_network

  db:
    image: postgres:15-alpine
    container_name: postgres_dev
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=appdb
    ports:
      - "5432:5432"  # Expose for direct access
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:

networks:
  app_network:
    driver: bridge
```

### Production Configuration

Production setup with resource limits, logging, and security:

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: fastapi_prod
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}  # Use secrets
      - ENVIRONMENT=production
      - DEBUG=false
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app_network
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
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    image: postgres:15-alpine
    container_name: postgres_prod
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app_network
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:

networks:
  app_network:
    driver: bridge
```

---

## Customization Notes

When generating configurations:

1. **Python version**: Match the version in `.python-version` or `pyproject.toml`
2. **Port numbers**: Check if default ports are available or need changing
3. **Database credentials**: Use strong passwords for production
4. **Service names**: Can be customized based on project naming
5. **Volume names**: Should match database type (postgres_data, mysql_data, etc.)
6. **Network names**: Can be customized but must match across services
7. **Health checks**: Adjust intervals based on service startup time
8. **Resource limits**: Set based on expected load and available resources

## Usage with FastAPI

Ensure your FastAPI app has a health check endpoint:

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

This allows Docker's health check to verify the service is running properly.

# Environment Variables Reference

Complete guide to type-safe configuration with pydantic-settings for managing secrets, API keys, and environment-specific settings.

## Table of Contents
- Why Environment Variables Matter
- pydantic-settings: Type-Safe Configuration
- Using Settings in Your App
- The .env File
- Critical: Gitignore Your Secrets
- Caching Settings
- Complete Settings Example
- Validation Errors
- Hands-On Exercise
- Common Mistakes
- Security Checklist

## Why Environment Variables Matter

**The Problem with Hardcoding:**

```python
# ❌ WRONG - Security risk! Secrets in code!
DATABASE_URL = "postgresql://user:password123@localhost/mydb"
API_KEY = "sk_live_abc123xyz789"
DEBUG = True

@app.get("/config")
def get_config():
    return {"database": DATABASE_URL, "api_key": API_KEY}
```

**What's wrong?**

1. **Security risk** - Secrets committed to version control, visible in logs, exposed in stack traces
2. **No environment flexibility** - Same settings for dev, staging, production
3. **Hard to change** - Need to modify code and redeploy to change a setting
4. **Secrets leak** - Anyone with code access has production credentials

**The Solution: Environment Variables**

```python
# ✅ CORRECT - Settings from environment
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    api_key: str
    debug: bool = False

    class Config:
        env_file = ".env"

@app.get("/config")
def get_config(settings: Settings = Depends(get_settings)):
    return {"database": settings.database_url[:20] + "...", "debug": settings.debug}
```

**Benefits:**

- Secrets never in code
- Different settings per environment
- Change without redeploying
- Type-safe configuration with validation

## pydantic-settings: Type-Safe Configuration

Pydantic-settings extends Pydantic to load configuration from environment variables with automatic type conversion and validation.

**Install:**

```bash
uv add pydantic-settings
```

**Basic pattern:**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "My API"
    debug: bool = False
    max_connections: int = 100

    class Config:
        env_file = ".env"  # Load from .env file

# Create settings instance
settings = Settings()
print(settings.app_name)  # "My API"
print(settings.debug)      # False
```

**Key features:**

- **Type conversion** - `"123"` becomes `int(123)`, `"true"` becomes `bool(True)`
- **Validation** - Invalid types raise errors at startup, not during requests
- **Defaults** - Optional settings with sensible defaults
- **Documentation** - Types make it clear what each setting expects

## Using Settings in Your App

The recommended pattern uses dependency injection with `Depends()`:

```python
from functools import lru_cache
from fastapi import Depends, FastAPI
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Task API"
    debug: bool = False

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()

app = FastAPI()

@app.get("/info")
def app_info(settings: Settings = Depends(get_settings)):
    return {"app_name": settings.app_name, "debug": settings.debug}
```

**Why this pattern?**

1. **Easy to test** - Override `get_settings` dependency in tests
2. **Cached** - `@lru_cache` loads settings once, not per-request
3. **Type-safe** - FastAPI knows the type, editors autocomplete
4. **Explicit** - Clear which endpoints use settings

## The .env File

The `.env` file stores environment variables for local development:

**Create `.env`:**

```bash
# .env
APP_NAME=My API
DEBUG=true
DATABASE_URL=postgresql://user:pass@localhost/db
API_KEY=sk_test_abc123
MAX_CONNECTIONS=50
```

**Tell pydantic-settings to load it:**

```python
class Settings(BaseSettings):
    app_name: str
    debug: bool = False
    database_url: str
    api_key: str
    max_connections: int = 100

    class Config:
        env_file = ".env"  # ← This loads .env automatically
```

**How it works:**

1. pydantic-settings looks for `.env` in the current directory
2. Reads `KEY=VALUE` pairs
3. Converts types based on your Settings class
4. Falls back to system environment variables if not in `.env`

**Environment variables override .env:**

```bash
# .env has DEBUG=false
# But you can override:
DEBUG=true uvicorn main:app
```

## Critical: Gitignore Your Secrets

**NEVER commit `.env` to version control!**

**Step 1: Add `.env` to `.gitignore`**

```bash
# .gitignore
.env
*.env
.env.local
.env.*.local
```

**Step 2: Create `.env.example` as a template**

```bash
# .env.example (committed to git)
APP_NAME=My API
DEBUG=false
DATABASE_URL=postgresql://user:password@localhost/dbname
API_KEY=your_api_key_here
MAX_CONNECTIONS=100
```

**Workflow:**

1. Developers clone the repo
2. Copy `.env.example` to `.env`: `cp .env.example .env`
3. Fill in real secrets in `.env`
4. `.env` stays local, never committed

**Why `.env.example`?**

- Documents what settings are needed
- Shows expected format
- Contains no real secrets
- Safe to commit

## Caching Settings

Settings don't change during runtime, so load them once with `@lru_cache`:

```python
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    """Load settings once, reuse forever."""
    return Settings()
```

**Without caching:**

```python
# ❌ Parses .env file on EVERY request!
def get_settings() -> Settings:
    return Settings()  # Expensive!

@app.get("/info")
def app_info(settings: Settings = Depends(get_settings)):
    return {"app": settings.app_name}
```

**With caching:**

```python
# ✅ Parses .env once at startup
@lru_cache
def get_settings() -> Settings:
    return Settings()  # Only runs once!

@app.get("/info")
def app_info(settings: Settings = Depends(get_settings)):
    return {"app": settings.app_name}
```

**Performance impact:**

- Without cache: Parse `.env` file 1000x per second under load
- With cache: Parse `.env` file once at startup

**When NOT to cache:**

- Settings that change at runtime (rare - use a database instead)
- Testing (override the dependency instead)

## Complete Settings Example

A production-ready settings class with database, auth, and API keys:

**config.py:**

```python
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    app_name: str = "Task API"
    debug: bool = False
    version: str = "1.0.0"

    # Database
    database_url: str = Field(..., description="PostgreSQL connection string")
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # Authentication
    secret_key: str = Field(..., min_length=32, description="JWT secret key")
    access_token_expire_minutes: int = 30

    # External APIs
    stripe_api_key: str = Field(..., description="Stripe API key")
    sendgrid_api_key: str = Field(..., description="SendGrid API key")

    # CORS
    allowed_origins: list[str] = Field(default=["http://localhost:3000"])

    class Config:
        env_file = ".env"
        case_sensitive = False  # Allow DATABASE_URL or database_url

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**.env:**

```bash
# Application
APP_NAME=Task API
DEBUG=true
VERSION=1.0.0

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/taskdb
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Authentication
SECRET_KEY=your-super-secret-key-min-32-chars-long-abc123xyz789
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External APIs
STRIPE_API_KEY=sk_test_abc123
SENDGRID_API_KEY=SG.abc123xyz789

# CORS (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

**Using in endpoints:**

```python
from fastapi import Depends, FastAPI
from config import Settings, get_settings

app = FastAPI()

@app.get("/info")
def app_info(settings: Settings = Depends(get_settings)):
    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "debug": settings.debug
    }

@app.post("/charge")
def create_charge(settings: Settings = Depends(get_settings)):
    # Use Stripe API key
    stripe.api_key = settings.stripe_api_key
    # ... charge logic
    return {"status": "charged"}
```

## Validation Errors

Pydantic validates settings at startup—if something's wrong, your app fails fast with helpful errors.

**Missing required field:**

```python
class Settings(BaseSettings):
    database_url: str  # Required!
    api_key: str      # Required!

    class Config:
        env_file = ".env"
```

**If .env is missing `DATABASE_URL`:**

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
database_url
  Field required [type=missing, input_value={}, input_type=dict]
```

**Wrong type:**

```bash
# .env
MAX_CONNECTIONS=not_a_number  # Should be int!
```

```python
class Settings(BaseSettings):
    max_connections: int
```

**Error:**

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
max_connections
  Input should be a valid integer, unable to parse string as an integer
```

**Why this matters:**

- **Fail fast** - Errors at startup, not in production
- **Clear messages** - Know exactly what's wrong
- **Type safety** - Can't accidentally use a string as an int

**Custom validation:**

```python
from pydantic import Field, field_validator

class Settings(BaseSettings):
    secret_key: str = Field(..., min_length=32)
    database_url: str

    @field_validator("database_url")
    def validate_postgres_url(cls, v: str) -> str:
        if not v.startswith("postgresql://"):
            raise ValueError("database_url must be a PostgreSQL URL")
        return v

    class Config:
        env_file = ".env"
```

## Hands-On Exercise

Build a FastAPI app with environment variables:

**Step 1: Install pydantic-settings**

```bash
uv add pydantic-settings
```

**Step 2: Create `config.py`**

```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "My API"
    debug: bool = False
    database_url: str
    api_key: str

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Step 3: Create `.env`**

```bash
APP_NAME=Task API
DEBUG=true
DATABASE_URL=postgresql://localhost/taskdb
API_KEY=sk_test_abc123
```

**Step 4: Add `.env` to `.gitignore`**

```bash
echo ".env" >> .gitignore
```

**Step 5: Create `.env.example`**

```bash
APP_NAME=My API
DEBUG=false
DATABASE_URL=postgresql://user:password@localhost/dbname
API_KEY=your_api_key_here
```

**Step 6: Use in `main.py`**

```python
from fastapi import Depends, FastAPI
from config import Settings, get_settings

app = FastAPI()

@app.get("/")
def root(settings: Settings = Depends(get_settings)):
    return {"app_name": settings.app_name, "debug": settings.debug}

@app.get("/config")
def show_config(settings: Settings = Depends(get_settings)):
    return {
        "app_name": settings.app_name,
        "debug": settings.debug,
        "database": settings.database_url[:20] + "...",  # Don't expose full URL!
        "api_key": settings.api_key[:8] + "..."  # Don't expose full key!
    }
```

**Step 7: Run and test**

```bash
uv run uvicorn main:app --reload
```

Visit `http://localhost:8000/config`:

```json
{
  "app_name": "Task API",
  "debug": true,
  "database": "postgresql://localho...",
  "api_key": "sk_test_..."
}
```

**Step 8: Test with different environment**

```bash
# Override DEBUG in production
DEBUG=false uv run uvicorn main:app
```

## Common Mistakes

**Mistake 1: Committing `.env` to git**

```bash
# ❌ WRONG - Secrets exposed!
git add .env
git commit -m "Add config"
git push  # ← Secrets now public!

# ✅ CORRECT - .env in .gitignore
echo ".env" >> .gitignore
git add .gitignore .env.example
git commit -m "Add config template"
```

**Mistake 2: Wrong environment variable names**

```python
class Settings(BaseSettings):
    database_url: str  # Expects DATABASE_URL in .env
```

```bash
# ❌ WRONG - Wrong name!
DB_URL=postgresql://localhost/db

# ✅ CORRECT - Matches field name
DATABASE_URL=postgresql://localhost/db
```

**Mistake 3: Forgetting `Config` class**

```python
# ❌ WRONG - Won't load .env!
class Settings(BaseSettings):
    app_name: str
    debug: bool

# ✅ CORRECT - Config class tells it to load .env
class Settings(BaseSettings):
    app_name: str
    debug: bool

    class Config:
        env_file = ".env"
```

**Mistake 4: Not caching settings**

```python
# ❌ WRONG - Parses .env on every request!
def get_settings() -> Settings:
    return Settings()

# ✅ CORRECT - Parse once, cache forever
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Mistake 5: Exposing secrets in responses**

```python
# ❌ WRONG - API key exposed in response!
@app.get("/config")
def show_config(settings: Settings = Depends(get_settings)):
    return {"api_key": settings.api_key}  # Full key visible!

# ✅ CORRECT - Mask or omit secrets
@app.get("/config")
def show_config(settings: Settings = Depends(get_settings)):
    return {
        "app_name": settings.app_name,
        "debug": settings.debug
        # Don't include api_key at all
    }
```

## Security Checklist

Before deploying, verify:

- [ ] `.env` is in `.gitignore`
- [ ] `.env.example` documents all required variables (no secrets)
- [ ] No secrets hardcoded in code
- [ ] Production uses different secrets than development
- [ ] Secrets never logged or returned in API responses
- [ ] Settings cached with `@lru_cache`
- [ ] Required fields fail fast at startup
- [ ] Sensitive fields use `Field(..., description="...")` for documentation

**Production deployment:**

```bash
# ❌ WRONG - Using .env in production
docker run myapp  # Uses .env file

# ✅ CORRECT - Environment variables from container orchestration
docker run -e DATABASE_URL=$PROD_DB_URL -e API_KEY=$PROD_API_KEY myapp
```

**Why?**

- `.env` files shouldn't exist in production
- Use container orchestration (Kubernetes secrets, Docker secrets, AWS Parameter Store)
- Environment variables injected at runtime
- Never commit production secrets

## Database Configuration

For SQLModel/PostgreSQL, add database settings to your Settings class:

```python
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    app_name: str = "Task API"
    debug: bool = False

    # Database
    database_url: str = Field(..., description="PostgreSQL connection string")

    class Config:
        env_file = ".env"
```

**For Neon PostgreSQL:**

```bash
# .env
DATABASE_URL=postgresql://user:password@ep-cool-term-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**IMPORTANT:** The `?sslmode=require` parameter is required for Neon connections!

**Connection string format:**

```
postgresql://[user]:[password]@[host]:[port]/[database]?[parameters]
```

**Example breakdown:**

```
postgresql://myuser:mypass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
           └─user─┘ └pass─┘ └──────────host──────────────────┘ └db─┘ └params─┘
```

**Common database URLs:**

```bash
# Neon (managed PostgreSQL)
DATABASE_URL=postgresql://user:pass@ep-xxx.region.aws.neon.tech/neondb?sslmode=require

# Local PostgreSQL
DATABASE_URL=postgresql://postgres:password@localhost:5432/mydb

# Heroku Postgres
DATABASE_URL=postgresql://user:pass@ec2-xxx.compute-1.amazonaws.com:5432/dbname

# Supabase
DATABASE_URL=postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres
```

**Using in SQLModel:**

```python
from sqlmodel import create_engine
from config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, echo=True)
```

**See [references/sqlmodel-database.md](sqlmodel-database.md) for complete database setup guide.**

## Key Points

- Never hardcode secrets, API keys, or environment-specific settings
- Use `pydantic-settings` with `BaseSettings` for type-safe configuration
- Add `.env` to `.gitignore` and create `.env.example` template
- Cache settings with `@lru_cache` on `get_settings()` function
- Use `Depends(get_settings)` for dependency injection
- Validation errors fail fast at startup with helpful messages
- Different environments use different `.env` files or environment variables
- Production uses container orchestration for secrets, not `.env` files

# Lifespan Events Reference

Complete guide to using lifespan events for startup and shutdown logic in FastAPI applications. Essential for agent APIs that need resources ready before handling requests.

## Table of Contents
- The Lifespan Pattern
- Sharing State with Endpoints
- Database Connection Pool
- Preloading ML Models
- Initializing External Clients
- Complete Lifespan Example
- Deprecated: on_event Decorator
- Hands-On Exercise
- Common Mistakes
- Why This Matters for Agents

## The Lifespan Pattern

**The Problem: Cold Starts**

Your agent API needs resources ready immediately:
- Database connection pool
- ML model loaded in memory
- External API clients initialized
- Caches warmed up

Without lifespan events, these resources are created on the first request—causing a slow cold start.

**The Solution: Lifespan Events**

Use the `@asynccontextmanager` pattern to run code at startup and shutdown:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Code here runs before first request
    print("Starting up...")
    app.state.cache = {}
    yield  # Server runs and handles requests
    # SHUTDOWN: Code here runs after server stops
    print("Shutting down...")
    app.state.cache.clear()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"message": "Hello World"}
```

**Execution flow:**

```
1. FastAPI starts
2. Lifespan startup code runs (before yield)
3. Server begins accepting requests
4. ... requests handled ...
5. Server receives shutdown signal (Ctrl+C, SIGTERM)
6. Lifespan shutdown code runs (after yield)
7. FastAPI exits
```

**Key concepts:**

- **Code before `yield`** - Runs at startup, before any request
- **Code after `yield`** - Runs at shutdown, after last request
- **`app.state`** - Share resources between startup and endpoints
- **`@asynccontextmanager`** - Async context manager decorator (from contextlib)
- **Pass to FastAPI()** - `app = FastAPI(lifespan=lifespan)`

## Sharing State with Endpoints

Use `app.state` to store resources initialized at startup:

**Basic pattern:**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Store resources in app.state
    app.state.database = connect_to_database()
    app.state.cache = {}
    yield
    # Cleanup
    app.state.database.close()

app = FastAPI(lifespan=lifespan)

@app.get("/items/{item_id}")
def get_item(item_id: int, request: Request):
    # Access via request.app.state
    db = request.app.state.database
    cache = request.app.state.cache

    # Check cache first
    if item_id in cache:
        return cache[item_id]

    # Query database
    item = db.get_item(item_id)
    cache[item_id] = item
    return item
```

**Important:**

- **Set in lifespan:** `app.state.resource = value`
- **Access in endpoints:** `request.app.state.resource`
- **Not `app.state` in endpoints** - You need `request.app.state`

**Why `request.app.state`?**

```python
# ❌ WRONG - app is not in endpoint scope
@app.get("/items")
def get_items():
    cache = app.state.cache  # Error! 'app' not defined in this scope
    return cache

# ✅ CORRECT - Access via request
@app.get("/items")
def get_items(request: Request):
    cache = request.app.state.cache
    return cache
```

**Multiple resources:**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize multiple resources
    app.state.db = create_database_pool()
    app.state.redis = create_redis_client()
    app.state.http_client = httpx.AsyncClient()
    app.state.ml_model = load_model()

    yield

    # Cleanup in reverse order
    await app.state.http_client.aclose()
    app.state.redis.close()
    await app.state.db.dispose()
```

## Database Connection Pool

Create a connection pool at startup, reuse across all requests:

**The Problem: Creating connections per request**

```python
# ❌ BAD - Creates new connection for every request
@app.get("/users")
def list_users():
    engine = create_engine(settings.database_url)  # Expensive!
    with Session(engine) as session:
        users = session.exec(select(User)).all()
    engine.dispose()
    return users
```

**The Solution: Connection pool in lifespan**

```python
from contextlib import asynccontextmanager
from sqlmodel import create_engine, Session, select
from fastapi import FastAPI, Request, Depends
from config import get_settings

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create engine and connection pool at startup
    app.state.engine = create_engine(
        settings.database_url,
        echo=True,
        pool_size=10,          # Keep 10 connections open
        max_overflow=20,       # Allow 20 additional connections
        pool_pre_ping=True,    # Verify connections before use
    )
    yield
    # Dispose engine at shutdown
    app.state.engine.dispose()

app = FastAPI(lifespan=lifespan)

# Dependency to get session from pool
def get_session(request: Request):
    engine = request.app.state.engine
    with Session(engine) as session:
        yield session

# Use in endpoints
@app.get("/users")
def list_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users
```

**Benefits:**

- ✅ Engine created once at startup
- ✅ Connection pool reused across requests
- ✅ Connections verified before use (pool_pre_ping)
- ✅ Graceful cleanup at shutdown

**Connection pool parameters:**

```python
create_engine(
    url,
    pool_size=10,           # Number of persistent connections
    max_overflow=20,        # Additional connections if pool is full
    pool_timeout=30,        # Wait 30s for available connection
    pool_recycle=3600,      # Recycle connections after 1 hour
    pool_pre_ping=True,     # Test connection before using
)
```

**For async databases (SQLAlchemy async):**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = create_async_engine(
        settings.database_url,
        echo=True,
        pool_size=10,
        max_overflow=20,
    )
    yield
    await app.state.engine.dispose()

async def get_session(request: Request):
    engine = request.app.state.engine
    async with AsyncSession(engine) as session:
        yield session
```

## Preloading ML Models

Load ML models at startup to avoid cold starts on first request:

**The Problem: Loading models per request**

```python
# ❌ BAD - Loads model for every request (slow!)
@app.post("/embed")
def embed_text(text: str):
    model = SentenceTransformer("all-MiniLM-L6-v2")  # 5+ seconds!
    embedding = model.encode(text)
    return {"embedding": embedding.tolist()}
```

**The Solution: Load once at startup**

```python
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, Request

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model at startup (happens once)
    print("Loading embedding model...")
    app.state.model = SentenceTransformer("all-MiniLM-L6-v2")
    print("Model loaded!")
    yield
    # Free memory at shutdown
    del app.state.model
    print("Model unloaded")

app = FastAPI(lifespan=lifespan)

@app.post("/embed")
def embed_text(text: str, request: Request):
    # Use preloaded model (fast!)
    model = request.app.state.model
    embedding = model.encode(text)
    return {"embedding": embedding.tolist()}
```

**Startup logs:**

```
INFO:     Started server process
Loading embedding model...
Model loaded!
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**First request is fast:**

```bash
curl -X POST http://localhost:8000/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'

# Response in 50ms (not 5 seconds!)
```

**Complete example with error handling:**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        print("Loading models...")

        # Load multiple models
        app.state.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        app.state.classifier_model = load_classifier("sentiment-model.pkl")

        print(f"Models loaded: {len([k for k in dir(app.state) if 'model' in k])} models")

        yield

    finally:
        # Cleanup (runs even if startup fails)
        print("Unloading models...")
        if hasattr(app.state, "embedding_model"):
            del app.state.embedding_model
        if hasattr(app.state, "classifier_model"):
            del app.state.classifier_model
        print("Models unloaded")
```

## Initializing External Clients

Initialize HTTP clients and external API clients at startup:

**The Problem: Creating clients per request**

```python
# ❌ BAD - Creates new client every request
@app.get("/github/{username}")
async def get_github_user(username: str):
    async with httpx.AsyncClient() as client:  # Expensive!
        response = await client.get(f"https://api.github.com/users/{username}")
        return response.json()
```

**The Solution: Reuse client across requests**

```python
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create HTTP client at startup
    app.state.http_client = httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
    )
    yield
    # Close client at shutdown
    await app.state.http_client.aclose()

app = FastAPI(lifespan=lifespan)

@app.get("/github/{username}")
async def get_github_user(username: str, request: Request):
    # Reuse client (fast!)
    client = request.app.state.http_client
    response = await client.get(f"https://api.github.com/users/{username}")
    return response.json()
```

**Anthropic API client:**

```python
import anthropic
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from config import get_settings

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Anthropic client
    app.state.anthropic_client = anthropic.AsyncAnthropic(
        api_key=settings.anthropic_api_key,
    )
    yield
    # Client cleanup (if needed)
    await app.state.anthropic_client.close()

app = FastAPI(lifespan=lifespan)

@app.post("/chat")
async def chat(message: str, request: Request):
    client = request.app.state.anthropic_client
    response = await client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": message}]
    )
    return {"response": response.content[0].text}
```

**OpenAI client:**

```python
from openai import AsyncOpenAI

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    yield
    await app.state.openai_client.close()

@app.post("/complete")
async def complete(prompt: str, request: Request):
    client = request.app.state.openai_client
    response = await client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=100
    )
    return {"completion": response.choices[0].text}
```

**Multiple clients:**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize all external clients
    app.state.http_client = httpx.AsyncClient()
    app.state.anthropic = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    app.state.openai = AsyncOpenAI(api_key=settings.openai_api_key)

    yield

    # Close all clients
    await app.state.http_client.aclose()
    await app.state.anthropic.close()
    await app.state.openai.close()
```

## Complete Lifespan Example

Production-ready lifespan with database, HTTP client, and cache:

**complete_example.py:**

```python
import logging
from contextlib import asynccontextmanager
from sqlmodel import create_engine, Session
import httpx
from fastapi import FastAPI, Request, Depends
from config import get_settings

# Setup
settings = get_settings()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize resources at startup, cleanup at shutdown.
    """
    logger.info("=" * 50)
    logger.info("STARTUP: Initializing resources...")

    try:
        # 1. Database connection pool
        logger.info("Creating database engine...")
        app.state.engine = create_engine(
            settings.database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
        logger.info("✓ Database engine created")

        # 2. HTTP client
        logger.info("Creating HTTP client...")
        app.state.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=10)
        )
        logger.info("✓ HTTP client created")

        # 3. Cache
        logger.info("Initializing cache...")
        app.state.cache = {}
        logger.info("✓ Cache initialized")

        # 4. External API clients (if needed)
        if hasattr(settings, "anthropic_api_key"):
            import anthropic
            logger.info("Initializing Anthropic client...")
            app.state.anthropic = anthropic.AsyncAnthropic(
                api_key=settings.anthropic_api_key
            )
            logger.info("✓ Anthropic client initialized")

        logger.info("✅ All resources initialized successfully")
        logger.info("=" * 50)

        yield  # Server runs here

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    finally:
        # SHUTDOWN: Cleanup resources
        logger.info("=" * 50)
        logger.info("SHUTDOWN: Cleaning up resources...")

        # Close in reverse order
        if hasattr(app.state, "anthropic"):
            logger.info("Closing Anthropic client...")
            await app.state.anthropic.close()
            logger.info("✓ Anthropic client closed")

        if hasattr(app.state, "cache"):
            logger.info("Clearing cache...")
            app.state.cache.clear()
            logger.info("✓ Cache cleared")

        if hasattr(app.state, "http_client"):
            logger.info("Closing HTTP client...")
            await app.state.http_client.aclose()
            logger.info("✓ HTTP client closed")

        if hasattr(app.state, "engine"):
            logger.info("Disposing database engine...")
            app.state.engine.dispose()
            logger.info("✓ Database engine disposed")

        logger.info("✅ All resources cleaned up")
        logger.info("=" * 50)

app = FastAPI(lifespan=lifespan)

# Dependency for database session
def get_session(request: Request):
    engine = request.app.state.engine
    with Session(engine) as session:
        yield session

# Example endpoints
@app.get("/")
def root():
    return {"message": "API is running", "status": "ok"}

@app.get("/health")
def health_check(request: Request):
    """Check if all resources are available."""
    health = {
        "status": "healthy",
        "database": hasattr(request.app.state, "engine"),
        "http_client": hasattr(request.app.state, "http_client"),
        "cache": hasattr(request.app.state, "cache"),
    }
    return health

@app.get("/users")
def list_users(session: Session = Depends(get_session)):
    """Example using database session."""
    # Query database using connection pool
    return {"users": []}
```

**Startup output:**

```
INFO:     Started server process [12345]
==================================================
STARTUP: Initializing resources...
Creating database engine...
✓ Database engine created
Creating HTTP client...
✓ HTTP client created
Initializing cache...
✓ Cache initialized
Initializing Anthropic client...
✓ Anthropic client initialized
✅ All resources initialized successfully
==================================================
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Shutdown output (Ctrl+C):**

```
INFO:     Shutting down
==================================================
SHUTDOWN: Cleaning up resources...
Closing Anthropic client...
✓ Anthropic client closed
Clearing cache...
✓ Cache cleared
Closing HTTP client...
✓ HTTP client closed
Disposing database engine...
✓ Database engine disposed
✅ All resources cleaned up
==================================================
INFO:     Finished server process [12345]
```

## Deprecated: on_event Decorator

**Old way (deprecated):**

```python
# ⚠️ DEPRECATED - Don't use this!
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
async def startup():
    app.state.db = create_database()
    app.state.cache = {}

@app.on_event("shutdown")
async def shutdown():
    app.state.db.close()
    app.state.cache.clear()
```

**New way (lifespan):**

```python
# ✅ MODERN - Use this!
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.db = create_database()
    app.state.cache = {}
    yield
    # Shutdown
    app.state.db.close()
    app.state.cache.clear()

app = FastAPI(lifespan=lifespan)
```

**Why lifespan is better:**

| Feature | on_event | lifespan |
|---------|----------|----------|
| **Status** | Deprecated | Recommended |
| **Error handling** | Separate try/except in each event | Single try/finally block |
| **Resource cleanup** | Manual in shutdown | Automatic with context manager |
| **Guarantees cleanup** | No - shutdown might not run | Yes - finally block always runs |
| **Testability** | Hard to test | Easy to test (context manager) |
| **Readability** | Scattered logic | Startup and shutdown together |

**Migration guide:**

```python
# BEFORE (deprecated)
@app.on_event("startup")
async def startup():
    app.state.resource = await create_resource()

@app.on_event("shutdown")
async def shutdown():
    await app.state.resource.close()

# AFTER (lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.resource = await create_resource()
    yield
    await app.state.resource.close()

app = FastAPI(lifespan=lifespan)
```

**Why was on_event deprecated?**

1. **No cleanup guarantee** - If startup fails, shutdown doesn't run
2. **Scattered logic** - Startup and shutdown in separate functions
3. **Testing difficulty** - Hard to test startup/shutdown as a unit
4. **No standard pattern** - Different from Python's context managers

## Hands-On Exercise

Build a FastAPI app with lifespan events:

**Step 1: Create basic lifespan**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up...")
    yield
    print("👋 Shutting down...")

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"message": "Hello World"}
```

**Step 2: Add cache to app.state**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up...")
    app.state.cache = {}
    print("Cache initialized")
    yield
    print("👋 Shutting down...")
    print(f"Cache had {len(app.state.cache)} items")
    app.state.cache.clear()

@app.get("/cache/{key}")
def get_cache(key: str, request: Request):
    return request.app.state.cache.get(key, "Not found")

@app.post("/cache/{key}")
def set_cache(key: str, value: str, request: Request):
    request.app.state.cache[key] = value
    return {"status": "cached", "key": key}
```

**Step 3: Add database pool**

```python
from sqlmodel import create_engine, Session
from config import get_settings

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up...")

    # Database
    print("Creating database engine...")
    app.state.engine = create_engine(
        settings.database_url,
        pool_size=5,
        max_overflow=10,
    )
    print("✓ Database engine created")

    # Cache
    app.state.cache = {}
    print("✓ Cache initialized")

    yield

    print("👋 Shutting down...")
    app.state.engine.dispose()
    print("✓ Database engine disposed")
    app.state.cache.clear()
    print("✓ Cache cleared")

def get_session(request: Request):
    engine = request.app.state.engine
    with Session(engine) as session:
        yield session
```

**Step 4: Test startup and shutdown**

```bash
# Start server
uv run uvicorn main:app --reload

# Output:
# 🚀 Starting up...
# Creating database engine...
# ✓ Database engine created
# ✓ Cache initialized
# INFO:     Application startup complete.

# Stop server (Ctrl+C)
# Output:
# 👋 Shutting down...
# ✓ Database engine disposed
# ✓ Cache cleared
```

**Step 5: Test cache**

```bash
# Set value
curl -X POST http://localhost:8000/cache/name -d "Alice"

# Get value
curl http://localhost:8000/cache/name
# "Alice"
```

## Common Mistakes

**Mistake 1: Forgetting to yield**

```python
# ❌ WRONG - Missing yield
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.cache = {}
    # Forgot yield!

# Error: async generator didn't yield

# ✅ CORRECT
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.cache = {}
    yield  # Must yield!
    app.state.cache.clear()
```

**Mistake 2: Not passing lifespan to FastAPI()**

```python
# ❌ WRONG - Lifespan not used
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.cache = {}
    yield

app = FastAPI()  # Forgot lifespan parameter!

# Lifespan never runs!

# ✅ CORRECT
app = FastAPI(lifespan=lifespan)
```

**Mistake 3: Accessing app.state incorrectly in endpoints**

```python
# ❌ WRONG - app not in scope
@app.get("/items")
def get_items():
    cache = app.state.cache  # Error! 'app' not defined
    return cache

# ✅ CORRECT - Use request.app.state
@app.get("/items")
def get_items(request: Request):
    cache = request.app.state.cache
    return cache
```

**Mistake 4: Not handling async cleanup**

```python
# ❌ WRONG - Forgot await for async cleanup
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient()
    yield
    app.state.client.aclose()  # Forgot await!

# ✅ CORRECT
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient()
    yield
    await app.state.client.aclose()
```

**Mistake 5: Using on_event (deprecated)**

```python
# ❌ DEPRECATED
@app.on_event("startup")
async def startup():
    app.state.cache = {}

# ✅ MODERN
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.cache = {}
    yield
```

**Mistake 6: Cleanup order matters**

```python
# ❌ WRONG - Closing database before cache that uses it
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = create_db()
    app.state.cache = Cache(app.state.db)  # Cache depends on db
    yield
    app.state.db.close()      # Close db first
    app.state.cache.close()   # Cache still needs db!

# ✅ CORRECT - Reverse order
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = create_db()
    app.state.cache = Cache(app.state.db)
    yield
    app.state.cache.close()   # Close cache first
    app.state.db.close()      # Then close db
```

## Why This Matters for Agents

Lifespan events are critical for agent-facing APIs:

### 1. No Cold Starts

**Problem:** First request is slow while loading resources.

```python
# ❌ Without lifespan - First request waits 5s to load model
@app.post("/embed")
def embed(text: str):
    model = load_model()  # 5 seconds on first request!
    return model.encode(text)
```

**Solution:** Preload at startup.

```python
# ✅ With lifespan - All requests are fast
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = load_model()  # 5 seconds at startup
    yield

@app.post("/embed")
def embed(text: str, request: Request):
    model = request.app.state.model  # Instant!
    return model.encode(text)
```

### 2. Graceful Shutdown

**Problem:** Server crashes leave resources open (connections, file handles).

**Solution:** Cleanup in shutdown phase.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = create_db_pool()
    yield
    # Always runs, even on crash
    app.state.db.dispose()
```

### 3. Resource Sharing

**Problem:** Creating clients per request is expensive.

**Solution:** Share one client across all requests.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # One client for all requests
    app.state.http_client = httpx.AsyncClient()
    yield
    await app.state.http_client.aclose()
```

### 4. Agent Performance

**Problem:** Agent APIs need consistent low latency.

**Solution:** Lifespan ensures resources are ready:

- ✅ Database connection pool ready
- ✅ ML models loaded in memory
- ✅ API clients initialized
- ✅ Caches warmed up

**Result:** Every request is fast, no variability.

## Key Points

- Use `@asynccontextmanager` with `yield` for lifespan events
- Code before `yield` runs at startup (before first request)
- Code after `yield` runs at shutdown (after last request)
- Use `app.state` to store resources initialized at startup
- Access resources via `request.app.state` in endpoints (not `app.state`)
- Pass lifespan to `FastAPI(lifespan=lifespan)`
- Create database connection pools at startup
- Preload ML models to avoid cold starts
- Initialize external API clients once and reuse
- Cleanup resources at shutdown (close connections, free memory)
- Use try/finally for guaranteed cleanup
- Cleanup in reverse order of initialization
- Lifespan replaces deprecated `@app.on_event()` decorator
- Await async cleanup operations (aclose, dispose)
- Log startup/shutdown for observability

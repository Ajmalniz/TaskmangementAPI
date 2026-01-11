# Middleware and CORS Reference

Complete guide to implementing middleware and configuring CORS in FastAPI applications for agent APIs.

## Table of Contents
- What Is Middleware?
- Creating Custom Middleware
- Request Logging Middleware
- Middleware Execution Order
- CORS: Cross-Origin Resource Sharing
- Configuring CORSMiddleware
- CORS Parameters
- Development vs Production
- Important CORS Rule
- Complete Middleware Setup
- Hands-On Exercise
- Common Mistakes
- Why This Matters for Agents
- Built-in Middleware
- Common Middleware Patterns

## What Is Middleware?

**Middleware sits at the door** of your FastAPI application, intercepting every incoming request and outgoing response.

**The Problem Without Middleware:**

```python
# ❌ Repetitive - Every endpoint needs the same code
import time

@app.get("/tasks")
def list_tasks():
    start = time.perf_counter()
    # ... endpoint logic ...
    duration = time.perf_counter() - start
    logger.info(f"GET /tasks took {duration}s")

@app.post("/tasks")
def create_task():
    start = time.perf_counter()
    # ... endpoint logic ...
    duration = time.perf_counter() - start
    logger.info(f"POST /tasks took {duration}s")

# Repeat for every endpoint!
```

**The Solution: Middleware**

```python
# ✅ Write once, applies to all endpoints
@app.middleware("http")
async def log_timing(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    logger.info(f"{request.method} {request.url.path} took {duration}s")
    return response
```

**Middleware execution flow:**

```
┌────────────────────────────────────────────────────────────┐
│                    INCOMING REQUEST                        │
└────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────┐
│                 Middleware 1 (BEFORE)                      │
│  - Extract token, log request, start timer                │
└────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────┐
│                 Middleware 2 (BEFORE)                      │
│  - Validate CORS, check rate limits                       │
└────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────┐
│               PATH OPERATION (ENDPOINT)                    │
│  - Your actual route handler code                         │
└────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────┐
│                 Middleware 2 (AFTER)                       │
│  - Add CORS headers                                        │
└────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────┐
│                 Middleware 1 (AFTER)                       │
│  - Add timing header, log response                        │
└────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────┐
│                    OUTGOING RESPONSE                       │
└────────────────────────────────────────────────────────────┘
```

**Key concept:** Middleware wraps your entire application. Code before `call_next()` runs on the way in, code after runs on the way out.

## Creating Custom Middleware

Use the `@app.middleware("http")` decorator for simple middleware:

**Basic pattern:**

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.middleware("http")
async def my_middleware(request: Request, call_next):
    # Code here runs BEFORE the endpoint
    print(f"Incoming: {request.method} {request.url.path}")

    # Pass request to next middleware or endpoint
    response = await call_next(request)

    # Code here runs AFTER the endpoint
    print(f"Outgoing: {response.status_code}")

    return response  # Must return response!
```

**Timing example with X-Process-Time header:**

```python
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response
```

**Test it:**

```bash
curl -I http://localhost:8000/tasks

# Response headers include:
# X-Process-Time: 0.0234
```

**Important:**

1. **Always `await call_next(request)`** - Passes control to next middleware/endpoint
2. **Always return the response** - If you forget, FastAPI will hang
3. **Must be `async def`** - Middleware runs asynchronously

## Request Logging Middleware

Log every incoming request and outgoing response:

```python
import logging
from fastapi import Request

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log incoming request
    logger.info(f"→ {request.method} {request.url.path} from {request.client.host}")

    # Process request
    response = await call_next(request)

    # Log outgoing response
    logger.info(f"← {request.method} {request.url.path} → {response.status_code}")

    return response
```

**Console output:**

```
2024-01-15 10:30:00 - __main__ - INFO - → GET /tasks from 127.0.0.1
2024-01-15 10:30:00 - __main__ - INFO - ← GET /tasks → 200

2024-01-15 10:30:05 - __main__ - INFO - → POST /tasks from 127.0.0.1
2024-01-15 10:30:05 - __main__ - INFO - ← POST /tasks → 201
```

**Enhanced logging with timing:**

```python
@app.middleware("http")
async def log_requests_with_timing(request: Request, call_next):
    start = time.perf_counter()

    logger.info(f"→ {request.method} {request.url.path}")

    response = await call_next(request)

    duration = time.perf_counter() - start
    logger.info(
        f"← {request.method} {request.url.path} "
        f"→ {response.status_code} in {duration:.4f}s"
    )

    return response
```

## Middleware Execution Order

**Middleware is a stack—last added is outermost:**

```python
app = FastAPI()

@app.middleware("http")
async def middleware_1(request: Request, call_next):
    print("1: Before")
    response = await call_next(request)
    print("1: After")
    return response

@app.middleware("http")
async def middleware_2(request: Request, call_next):
    print("2: Before")
    response = await call_next(request)
    print("2: After")
    return response

@app.middleware("http")
async def middleware_3(request: Request, call_next):
    print("3: Before")
    response = await call_next(request)
    print("3: After")
    return response

@app.get("/test")
def test_endpoint():
    print("ENDPOINT")
    return {"message": "test"}
```

**Request to `/test` produces:**

```
3: Before    ← Outermost (added last)
2: Before
1: Before    ← Innermost (added first)
ENDPOINT     ← Your route handler
1: After
2: After
3: After     ← Returns to client
```

**Key insight:** Think of middleware as layers of an onion. The last middleware added is the outermost layer.

**With `app.add_middleware()` (class-based):**

```python
from starlette.middleware.base import BaseHTTPMiddleware

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Process-Time"] = str(time.perf_counter() - start)
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"→ {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"← {response.status_code}")
        return response

# Add in reverse order (last = outermost)
app.add_middleware(TimingMiddleware)   # Inner
app.add_middleware(LoggingMiddleware)  # Outer

# Execution:
# Request:  LoggingMiddleware → TimingMiddleware → endpoint
# Response: endpoint → TimingMiddleware → LoggingMiddleware
```

## CORS: Cross-Origin Resource Sharing

**The Problem: Browsers Block Cross-Origin Requests**

Your API runs on `http://localhost:8000`. Your frontend runs on `http://localhost:3000`. When the frontend tries to call your API, the browser blocks it:

```javascript
// Frontend at http://localhost:3000
fetch("http://localhost:8000/tasks")
  .then(response => response.json())
  .catch(error => console.error(error));

// Browser console:
// ❌ Access to fetch at 'http://localhost:8000/tasks' from origin
// 'http://localhost:3000' has been blocked by CORS policy
```

**Why?** Browsers enforce the **Same-Origin Policy** for security. An origin = protocol + domain + port.

**Different origins:**

| Frontend Origin | API Origin | Same Origin? |
|----------------|------------|--------------|
| `http://localhost:3000` | `http://localhost:8000` | ❌ Different port |
| `https://app.com` | `http://app.com` | ❌ Different protocol |
| `http://app.com` | `http://api.app.com` | ❌ Different subdomain |
| `http://app.com:80` | `http://app.com:80` | ✅ Same origin |

**The Solution: CORS Headers**

Your API tells the browser "I allow requests from specific origins" using HTTP headers:

```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Allow-Credentials: true
```

FastAPI's `CORSMiddleware` adds these headers automatically.

## Configuring CORSMiddleware

**Basic setup:**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**This allows:**

- ✅ Frontend at `http://localhost:3000` can call your API
- ✅ All HTTP methods (GET, POST, PUT, DELETE, etc.)
- ✅ All request headers
- ✅ Cookies and Authorization headers (credentials)

**Multiple origins:**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "https://myapp.com",
        "https://www.myapp.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## CORS Parameters

Comprehensive guide to all CORS configuration options:

### allow_origins

**Purpose:** List of origins allowed to make requests.

```python
# Specific origins
allow_origins=["http://localhost:3000", "https://myapp.com"]

# Allow all origins (development only!)
allow_origins=["*"]
```

**Examples:**

- `"http://localhost:3000"` - React dev server
- `"https://myapp.com"` - Production frontend
- `"https://staging.myapp.com"` - Staging environment
- `["*"]` - Any origin (NOT for production with credentials!)

### allow_methods

**Purpose:** HTTP methods allowed from other origins.

```python
# Allow all methods
allow_methods=["*"]

# Specific methods
allow_methods=["GET", "POST", "PUT", "DELETE"]

# Read-only API
allow_methods=["GET", "HEAD", "OPTIONS"]
```

**Common values:**

- `["*"]` - All methods (GET, POST, PUT, DELETE, PATCH, OPTIONS, etc.)
- `["GET", "POST"]` - Read and create only
- `["GET"]` - Read-only access

### allow_headers

**Purpose:** HTTP headers allowed in requests from other origins.

```python
# Allow all headers
allow_headers=["*"]

# Specific headers
allow_headers=["Authorization", "Content-Type", "X-Request-ID"]
```

**Common values:**

- `["*"]` - All headers
- `["Authorization"]` - For JWT tokens
- `["Content-Type"]` - For JSON requests
- `["X-Custom-Header"]` - Custom headers

### allow_credentials

**Purpose:** Allow cookies, Authorization headers, and TLS client certificates.

```python
# Allow credentials (cookies, auth headers)
allow_credentials=True

# Disallow credentials (public API)
allow_credentials=False
```

**CRITICAL RULE:** Cannot use `allow_origins=["*"]` with `allow_credentials=True`!

```python
# ❌ WRONG - Security error!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # Error! Cannot use * with credentials
)

# ✅ CORRECT - Specific origins with credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://myapp.com"],
    allow_credentials=True,
)
```

### expose_headers

**Purpose:** Response headers visible to JavaScript in the browser.

```python
expose_headers=["X-Total-Count", "X-Page-Size", "X-Process-Time"]
```

By default, browsers only expose:
- `Cache-Control`
- `Content-Language`
- `Content-Type`
- `Expires`
- `Last-Modified`
- `Pragma`

If you add custom headers (like `X-Process-Time`), you must expose them:

```python
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.perf_counter() - start)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    expose_headers=["X-Process-Time"],  # Make it visible to JavaScript
)
```

Frontend can now read it:

```javascript
fetch("http://localhost:8000/tasks")
  .then(response => {
    console.log(response.headers.get("X-Process-Time"));  // Works!
  });
```

### max_age

**Purpose:** How long (in seconds) the browser caches CORS preflight responses.

```python
max_age=3600  # Cache for 1 hour
```

**What is a preflight request?**

For some requests, browsers send an OPTIONS request first to check if CORS is allowed:

```
OPTIONS /tasks HTTP/1.1
Origin: http://localhost:3000
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Authorization
```

The server responds with allowed methods/headers. `max_age` tells the browser how long to cache this response.

**Values:**

- `600` - 10 minutes (default)
- `3600` - 1 hour
- `86400` - 24 hours

## Development vs Production

### Development Configuration

**Allow everything for rapid iteration:**

```python
# development.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Any origin
    allow_credentials=False,  # Must be False with "*"
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Use case:** Local development, testing, prototyping.

**Warning:** Never deploy this to production!

### Production Configuration

**Explicit origins and restricted access:**

```python
# production.py
from config import get_settings

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # From environment variable
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Total-Count", "X-Process-Time"],
    max_age=3600,
)
```

**config.py:**

```python
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )

    class Config:
        env_file = ".env"
```

**.env:**

```bash
# Development
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# Production
CORS_ORIGINS=["https://myapp.com","https://www.myapp.com","https://app.myapp.com"]
```

**Use case:** Production deployment with specific frontend domains.

## Important CORS Rule

**YOU CANNOT USE `["*"]` WITH `allow_credentials=True`!**

This is a security restriction in the CORS specification.

```python
# ❌ WRONG - Browser will reject this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # Error!
)

# Browser error:
# "The value of the 'Access-Control-Allow-Origin' header in the response
# must not be the wildcard '*' when the request's credentials mode is 'include'"
```

**Why?** Allowing credentials from any origin would be a massive security hole. Browsers prevent this.

**Solutions:**

1. **Use specific origins:**

```python
# ✅ CORRECT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://myapp.com"],
    allow_credentials=True,
)
```

2. **Or disable credentials:**

```python
# ✅ CORRECT (public API, no auth)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
)
```

## Complete Middleware Setup

Production-ready example combining CORS, timing, and logging:

**main.py:**

```python
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings

# Setup
app = FastAPI()
settings = get_settings()
logger = logging.getLogger(__name__)

# 1. CORS (added first = innermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Process-Time", "X-Request-ID"],
    max_age=3600,
)

# 2. Timing (added second = middle)
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response

# 3. Logging (added last = outermost)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"← {response.status_code}")
    return response

# Routes
@app.get("/")
def root():
    return {"message": "Hello World"}
```

**Execution order for a request:**

```
Request arrives
  │
  ├→ Logging (before): Log "→ GET /"
  │   │
  │   ├→ Timing (before): Start timer
  │   │   │
  │   │   ├→ CORS (before): Check origin
  │   │   │   │
  │   │   │   ├→ ENDPOINT: Execute root()
  │   │   │   │
  │   │   │   └← CORS (after): Add CORS headers
  │   │   │
  │   │   └← Timing (after): Add X-Process-Time header
  │   │
  │   └← Logging (after): Log "← 200"
  │
Response sent to client
```

## Hands-On Exercise

Build a complete middleware setup with timing, logging, and CORS:

**Step 1: Add timing middleware**

```python
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response
```

**Step 2: Add logging middleware**

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"← {response.status_code} in {response.headers.get('X-Process-Time')}s")
    return response
```

**Step 3: Configure CORS**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],
)
```

**Step 4: Test with curl**

```bash
# Test timing header
curl -I http://localhost:8000/

# Response includes:
# X-Process-Time: 0.0023
```

**Step 5: Test CORS with OPTIONS request**

```bash
# Preflight request
curl -X OPTIONS http://localhost:8000/tasks \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -i

# Response includes:
# Access-Control-Allow-Origin: http://localhost:3000
# Access-Control-Allow-Methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
# Access-Control-Allow-Headers: authorization, content-type
```

**Step 6: Verify headers in browser**

Create a simple HTML file:

```html
<!-- test.html -->
<!DOCTYPE html>
<html>
<body>
  <script>
    fetch("http://localhost:8000/")
      .then(response => {
        console.log("Status:", response.status);
        console.log("X-Process-Time:", response.headers.get("X-Process-Time"));
        return response.json();
      })
      .then(data => console.log("Data:", data))
      .catch(error => console.error("Error:", error));
  </script>
</body>
</html>
```

Open with:

```bash
# Serve on port 3000
python -m http.server 3000
```

Open http://localhost:3000/test.html and check browser console.

## Common Mistakes

**Mistake 1: Forgetting to await `call_next`**

```python
# ❌ WRONG - Missing await
@app.middleware("http")
async def my_middleware(request: Request, call_next):
    response = call_next(request)  # Forgot await!
    return response

# Error: coroutine 'call_next' was never awaited

# ✅ CORRECT
@app.middleware("http")
async def my_middleware(request: Request, call_next):
    response = await call_next(request)
    return response
```

**Mistake 2: Using credentials with wildcard origin**

```python
# ❌ WRONG - Browser will reject
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # Cannot use with "*"
)

# ✅ CORRECT - Specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://myapp.com"],
    allow_credentials=True,
)
```

**Mistake 3: Not returning response**

```python
# ❌ WRONG - Forgot to return
@app.middleware("http")
async def my_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Custom"] = "value"
    # Forgot return!

# FastAPI hangs, no response sent

# ✅ CORRECT
@app.middleware("http")
async def my_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Custom"] = "value"
    return response
```

**Mistake 4: Wrong execution order**

```python
# ❌ CONFUSING - Order matters!
# CORS added last = outermost
app.add_middleware(TimingMiddleware)
app.add_middleware(CORSMiddleware)

# Result: CORS runs first, timing runs second
# CORS headers might not be added if timing fails

# ✅ BETTER - CORS first (innermost)
app.add_middleware(CORSMiddleware)
app.add_middleware(TimingMiddleware)

# Result: Timing runs first, CORS headers always added
```

**Mistake 5: Modifying request after `call_next`**

```python
# ❌ WRONG - Too late!
@app.middleware("http")
async def my_middleware(request: Request, call_next):
    response = await call_next(request)
    request.headers["X-Custom"] = "value"  # Too late! Request already processed
    return response

# ✅ CORRECT - Modify before call_next
@app.middleware("http")
async def my_middleware(request: Request, call_next):
    request.state.custom_value = "value"  # Modify before
    response = await call_next(request)
    return response
```

**Mistake 6: Not exposing custom headers**

```python
# ❌ WRONG - Frontend can't read X-Process-Time
@app.middleware("http")
async def add_timing(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.perf_counter() - start)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    # Missing expose_headers!
)

# ✅ CORRECT - Expose custom headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    expose_headers=["X-Process-Time"],
)
```

## Why This Matters for Agents

Middleware solves critical problems for agent-facing APIs:

### 1. Frontends Need CORS

**Problem:** React/Vue/Svelte frontends run on different ports than your API.

```javascript
// Frontend at http://localhost:3000
// API at http://localhost:8000
fetch("http://localhost:8000/api/tasks")  // Blocked by CORS!
```

**Solution:** CORSMiddleware allows specific origins.

### 2. Timing for Agent Responses

**Problem:** Agents need fast responses. Slow APIs cause timeout errors.

**Solution:** Add `X-Process-Time` header to track request duration.

```bash
curl -I http://localhost:8000/tasks

# X-Process-Time: 0.0234
# X-Process-Time: 2.1234  ← Slow! Investigate!
```

### 3. Logging for Debugging

**Problem:** When agents fail, you need to see what requests they made.

**Solution:** Middleware logs every request/response.

```
→ POST /tasks from 127.0.0.1
← POST /tasks → 422 (validation error)
```

You can immediately see the agent sent invalid data.

### 4. Consistent Headers

**Problem:** Every response needs certain headers (CORS, timing, request ID).

**Solution:** Middleware adds headers to ALL responses automatically.

```python
@app.middleware("http")
async def add_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = str(time.perf_counter() - start)
    return response
```

Every response now has tracking headers—no need to add them manually to each endpoint.

## Built-in Middleware

FastAPI includes several useful middleware classes:

### TrustedHostMiddleware

Protect against Host header attacks:

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com", "localhost"]
)
```

### GZipMiddleware

Compress responses to reduce bandwidth:

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

Compresses responses larger than 1000 bytes.

### HTTPSRedirectMiddleware

Force HTTPS in production:

```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
```

Redirects all HTTP requests to HTTPS.

## Common Middleware Patterns

### Request ID Tracking

Add unique ID to every request for tracing:

```python
import uuid
from fastapi import Request

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

Access in endpoints:

```python
@app.get("/tasks")
def list_tasks(request: Request):
    logger.info(f"Request {request.state.request_id}: listing tasks")
    return tasks
```

### Security Headers

Add security headers to all responses:

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

### Error Handling

Catch exceptions and return consistent error responses:

```python
from fastapi.responses import JSONResponse

@app.middleware("http")
async def catch_exceptions(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
```

## Key Points

- Middleware intercepts every request and response
- Write once, applies to all endpoints automatically
- Use `@app.middleware("http")` for simple middleware
- Always `await call_next(request)` and return response
- Middleware executes in reverse order (last added = outermost)
- CORS allows frontends on different origins to call your API
- Cannot use `allow_origins=["*"]` with `allow_credentials=True`
- Use explicit origins in production, `["*"]` only for development
- Expose custom headers with `expose_headers` parameter
- Add timing headers to track slow requests
- Log requests/responses for debugging
- Production setup: CORS from environment variables + timing + logging

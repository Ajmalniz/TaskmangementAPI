# JWT Authentication Reference

Complete guide to implementing stateless authentication with JSON Web Tokens (JWT) in FastAPI. Learn how users log in, receive tokens, and access protected routes.

## Table of Contents
- How JWT Works
- Installing Dependencies
- JWT Configuration
- Token Functions
- Login Endpoint
- Protecting Routes
- Protecting Task Routes
- Swagger UI Integration
- The Authentication Flow
- Hands-On Exercise
- Common Mistakes

## How JWT Works

**The Problem: HTTP is Stateless**

HTTP doesn't remember who you are between requests. Traditional solutions use sessions stored on the server, but this doesn't scale well for distributed systems or APIs.

**The Solution: JWT (JSON Web Tokens)**

JWTs provide **stateless authentication**:

1. User logs in with email/password
2. Server verifies credentials and creates a signed JWT
3. User includes JWT in `Authorization` header for subsequent requests
4. Server validates JWT signature and extracts user identity
5. No session storage needed—everything is in the token

**JWT Structure:**

A JWT has three parts separated by dots:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZUBleGFtcGxlLmNvbSIsImV4cCI6MTcwNTMyMDAwMH0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
└──────────── header ────────────┘ └─────────────── payload ───────────────┘ └────────────── signature ──────────────┘
```

**Parts breakdown:**

1. **Header** (Base64URL encoded JSON):
   ```json
   {
     "alg": "HS256",
     "typ": "JWT"
   }
   ```
   Algorithm used for signing (HS256 = HMAC SHA-256)

2. **Payload** (Base64URL encoded JSON):
   ```json
   {
     "sub": "alice@example.com",
     "exp": 1705320000
   }
   ```
   - `sub` (subject) - User identifier (email)
   - `exp` (expiration) - Token expiration timestamp

3. **Signature**:
   ```
   HMACSHA256(
     base64UrlEncode(header) + "." + base64UrlEncode(payload),
     secret_key
   )
   ```
   Ensures token wasn't tampered with

**Key Properties:**

- **Signed, not encrypted** - Anyone can decode and read the payload (don't put secrets in it!)
- **Tamper-proof** - Changing payload invalidates signature (only server with secret key can create valid tokens)
- **Stateless** - Server doesn't store sessions, just validates signature
- **Self-contained** - Token contains all needed information (user identity, expiration)

**Token Flow:**

```
1. Login:
   Client → POST /token (email, password)
   Server → Verifies password, creates JWT
   Server → {"access_token": "eyJ...", "token_type": "bearer"}

2. Authenticated Request:
   Client → GET /users/me
   Header: Authorization: Bearer eyJ...
   Server → Validates signature, extracts email
   Server → Returns user data

3. Protected Resource:
   Client → POST /tasks (title, description)
   Header: Authorization: Bearer eyJ...
   Server → Validates token, gets current user
   Server → Creates task owned by user
```

## Installing Dependencies

Install `python-jose` for JWT encoding/decoding:

```bash
uv add "python-jose[cryptography]"
```

**What gets installed:**

- `python-jose` - JWT library for Python
- `cryptography` - Cryptographic primitives (via `[cryptography]` extra)

**Why python-jose?**

- Standard library for JWT in Python
- Supports multiple algorithms (HS256, RS256, etc.)
- Well-documented and widely used
- Works seamlessly with FastAPI

**Alternative libraries:**

```bash
# Also valid, but python-jose is more common
uv add pyjwt[crypto]
```

We use `python-jose` because it's the standard in FastAPI tutorials and has excellent community support.

## JWT Configuration

Add JWT settings to your configuration:

**Update `config.py`:**

```python
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str

    # JWT Configuration
    secret_key: str = Field(..., description="Secret key for JWT signing")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Token expiration in minutes")

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Update `.env`:**

```bash
# Database
DATABASE_URL=postgresql://...

# JWT Configuration
SECRET_KEY=your-super-secret-key-here-at-least-32-characters-long-abc123xyz789
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Generate a secure secret key:**

```bash
# Use openssl to generate a secure random key
openssl rand -hex 32
```

**Output (example):**

```
8f3e2a1b9c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f
```

Copy this to your `.env` file:

```bash
SECRET_KEY=8f3e2a1b9c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f
```

**CRITICAL SECURITY NOTES:**

- Never commit the secret key to version control
- Use a different secret key for production
- At least 32 characters long
- Generate with a cryptographically secure random generator (like openssl)

**Update `.env.example`:**

```bash
# JWT Configuration
SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Token Functions

Create `auth.py` for JWT operations:

**auth.py:**

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from config import get_settings

settings = get_settings()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary with claims to encode (typically {"sub": email})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT string

    Example:
        >>> token = create_access_token({"sub": "alice@example.com"})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})

    # Encode and sign the JWT
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT string to decode

    Returns:
        Decoded payload dictionary

    Raises:
        JWTError: If token is invalid or expired

    Example:
        >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        >>> payload = decode_token(token)
        >>> print(payload["sub"])
        alice@example.com
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        raise
```

**How `create_access_token()` works:**

```python
# Create token for a user
token = create_access_token({"sub": "alice@example.com"})

# Behind the scenes:
# 1. Copy data: {"sub": "alice@example.com"}
# 2. Add expiration: {"sub": "alice@example.com", "exp": 1705320000}
# 3. Encode header: {"alg": "HS256", "typ": "JWT"}
# 4. Sign: HMACSHA256(header + payload, secret_key)
# 5. Return: "eyJ..." (base64url(header).base64url(payload).signature)
```

**How `decode_token()` works:**

```python
# Decode token
payload = decode_token("eyJ...")

# Behind the scenes:
# 1. Split token into parts: header, payload, signature
# 2. Verify signature: HMACSHA256(header + payload, secret_key) == signature
# 3. Check expiration: payload["exp"] > now
# 4. Return payload: {"sub": "alice@example.com", "exp": 1705320000}
```

**Token expiration:**

```python
# Default expiration (from settings)
token = create_access_token({"sub": "alice@example.com"})
# Expires in 30 minutes (settings.access_token_expire_minutes)

# Custom expiration
from datetime import timedelta
token = create_access_token(
    {"sub": "alice@example.com"},
    expires_delta=timedelta(hours=24)
)
# Expires in 24 hours
```

## Login Endpoint

Implement the `/token` endpoint for user login:

**main.py:**

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from database import get_session
from models import User
from security import verify_password
from auth import create_access_token

app = FastAPI()

@app.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    """
    OAuth2 compatible token login endpoint.

    Args:
        form_data: OAuth2PasswordRequestForm with username and password
        session: Database session

    Returns:
        {"access_token": "...", "token_type": "bearer"}

    Raises:
        401: Invalid credentials
    """
    # Step 1: Find user by email
    # Note: OAuth2 spec uses "username", but we use it for email
    statement = select(User).where(User.email == form_data.username)
    user = session.exec(statement).first()

    # Step 2: Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Step 3: Create access token
    access_token = create_access_token({"sub": user.email})

    # Step 4: Return token in OAuth2 format
    return {"access_token": access_token, "token_type": "bearer"}
```

**Important details:**

1. **OAuth2PasswordRequestForm**
   - Expects form data (not JSON!)
   - Fields: `username` and `password`
   - We use `username` field for email (OAuth2 spec)

2. **Generic error message**
   - "Incorrect email or password" (not "Email not found" or "Wrong password")
   - Prevents user enumeration attacks
   - Both cases return the same error

3. **WWW-Authenticate header**
   - Required for 401 responses
   - Tells client which authentication method to use
   - Value: "Bearer" for JWT tokens

4. **Token payload**
   - `{"sub": user.email}` - "sub" is the standard claim for user identity
   - Only include user identifier, not sensitive data
   - Token is signed, not encrypted—anyone can read it!

5. **Response format**
   - `{"access_token": "...", "token_type": "bearer"}`
   - OAuth2 standard format
   - Swagger UI expects this exact format

**Testing the login endpoint:**

```bash
# Login with form data (note: -d for form data, not -H "Content-Type: application/json")
curl -X POST http://localhost:8000/token \
  -d "username=alice@example.com" \
  -d "password=MySecurePassword123"
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZUBleGFtcGxlLmNvbSIsImV4cCI6MTcwNTMyMDAwMH0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
  "token_type": "bearer"
}
```

**Decode the token to see what's inside:**

```python
# You can decode on https://jwt.io or with python-jose
from jose import jwt

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
print(payload)
# {"sub": "alice@example.com", "exp": 1705320000}
```

## Protecting Routes

Use OAuth2PasswordBearer and a dependency to protect routes:

**main.py:**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlmodel import Session, select
from database import get_session
from models import User
from auth import decode_token

# OAuth2 scheme - tells FastAPI where to get the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header
        session: Database session

    Returns:
        User object for authenticated user

    Raises:
        401: Invalid or expired token, or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token
        payload = decode_token(token)
        email: str = payload.get("sub")

        if email is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Find user in database
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()

    if user is None:
        raise credentials_exception

    return user

# Protected route - requires authentication
@app.get("/users/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at
    }
```

**How `get_current_user` works:**

1. `OAuth2PasswordBearer(tokenUrl="token")` extracts token from `Authorization: Bearer <token>` header
2. `decode_token(token)` validates signature and expiration
3. Extract email from `payload["sub"]`
4. Query database to find user
5. Return `User` object

**Using protected routes:**

```bash
# Get token first
TOKEN=$(curl -X POST http://localhost:8000/token \
  -d "username=alice@example.com" \
  -d "password=MySecurePassword123" \
  | jq -r '.access_token')

# Use token to access protected route
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**

```json
{
  "id": 1,
  "email": "alice@example.com",
  "created_at": "2024-01-15T10:30:00"
}
```

**Without token:**

```bash
curl http://localhost:8000/users/me
```

**Response:**

```json
{
  "detail": "Not authenticated"
}
```

**With invalid token:**

```bash
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer invalid-token"
```

**Response:**

```json
{
  "detail": "Could not validate credentials"
}
```

## Protecting Task Routes

Associate tasks with users and filter by owner:

**Update Task model in `models.py`:**

```python
from sqlmodel import SQLModel, Field
from typing import Optional

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    status: str = Field(default="pending")
    owner_id: int = Field(foreign_key="user.id")  # User who owns this task

class TaskCreate(SQLModel):
    title: str
    description: Optional[str] = None

class TaskResponse(SQLModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    owner_id: int
```

**Protected task endpoints in `main.py`:**

```python
from models import Task, TaskCreate, TaskResponse

# CREATE - Requires authentication
@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a task for the current user."""
    db_task = Task(
        title=task.title,
        description=task.description,
        owner_id=current_user.id  # Associate with current user
    )
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

# READ LIST - Only user's own tasks
@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List all tasks for the current user."""
    statement = select(Task).where(Task.owner_id == current_user.id)
    tasks = session.exec(statement).all()
    return tasks

# READ SINGLE - Check ownership
@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a specific task (must be owned by current user)."""
    task = session.get(Task, task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check ownership
    if task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")

    return task

# UPDATE - Check ownership
@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a task (must be owned by current user)."""
    task = session.get(Task, task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this task")

    task.title = task_update.title
    task.description = task_update.description

    session.add(task)
    session.commit()
    session.refresh(task)
    return task

# DELETE - Check ownership
@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a task (must be owned by current user)."""
    task = session.get(Task, task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this task")

    session.delete(task)
    session.commit()
    return {"message": "Task deleted", "task_id": task_id}
```

**Key patterns:**

1. **Create** - Automatically set `owner_id` to current user
2. **List** - Filter by `owner_id == current_user.id`
3. **Read/Update/Delete** - Check ownership before allowing operation
4. **403 vs 404** - Return 404 if task doesn't exist, 403 if exists but not owned

**Testing protected task routes:**

```bash
# Login to get token
TOKEN=$(curl -X POST http://localhost:8000/token \
  -d "username=alice@example.com" \
  -d "password=MySecurePassword123" \
  | jq -r '.access_token')

# Create a task
curl -X POST http://localhost:8000/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My task", "description": "Task description"}'

# List tasks (only sees own tasks)
curl http://localhost:8000/tasks \
  -H "Authorization: Bearer $TOKEN"
```

## Swagger UI Integration

FastAPI's interactive documentation has built-in OAuth2 support:

**Access Swagger UI:**

```
http://localhost:8000/docs
```

**Using the Authorize button:**

1. Click the **"Authorize"** button (lock icon) in the top right
2. Enter credentials:
   - **username**: `alice@example.com`
   - **password**: `MySecurePassword123`
3. Click **"Authorize"**
4. Swagger UI calls `/token` and stores the access token
5. All subsequent requests automatically include `Authorization: Bearer <token>`
6. Lock icon changes to indicate authenticated state

**Testing protected endpoints:**

1. Try `/users/me` - Click "Try it out" → "Execute"
2. Response includes current user data
3. Token is automatically included in the request

**How it works:**

- `OAuth2PasswordBearer(tokenUrl="token")` tells Swagger UI where to get tokens
- Swagger UI renders an authentication form
- After login, tokens are stored in browser and included in all requests
- No need to manually add Authorization headers!

**Logout:**

- Click "Authorize" button again
- Click "Logout" to clear the token
- Requests will no longer include Authorization header

## The Authentication Flow

Complete flow from signup to protected routes:

```
┌─────────────────────────────────────────────────────────────────┐
│                        1. SIGNUP                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client                                       Server            │
│    │                                            │               │
│    │  POST /users/signup                        │               │
│    │  {"email": "alice@...", "password": "..."} │               │
│    ├───────────────────────────────────────────>│               │
│    │                                            │               │
│    │                          Hash password     │               │
│    │                          Store in database │               │
│    │                                            │               │
│    │  201 Created                               │               │
│    │  {"id": 1, "email": "alice@..."}           │               │
│    │<───────────────────────────────────────────┤               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        2. LOGIN                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client                                       Server            │
│    │                                            │               │
│    │  POST /token (form data)                   │               │
│    │  username=alice@...&password=...           │               │
│    ├───────────────────────────────────────────>│               │
│    │                                            │               │
│    │                          Find user         │               │
│    │                          Verify password   │               │
│    │                          Create JWT        │               │
│    │                                            │               │
│    │  200 OK                                    │               │
│    │  {"access_token": "eyJ...", "token_type": "bearer"} │     │
│    │<───────────────────────────────────────────┤               │
│    │                                            │               │
│    │  Store token                               │               │
│    │                                            │               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   3. PROTECTED REQUEST                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client                                       Server            │
│    │                                            │               │
│    │  GET /users/me                             │               │
│    │  Authorization: Bearer eyJ...              │               │
│    ├───────────────────────────────────────────>│               │
│    │                                            │               │
│    │                          Extract token     │               │
│    │                          Validate signature│               │
│    │                          Decode payload    │               │
│    │                          Find user by email│               │
│    │                                            │               │
│    │  200 OK                                    │               │
│    │  {"id": 1, "email": "alice@..."}           │               │
│    │<───────────────────────────────────────────┤               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  4. CREATE PROTECTED RESOURCE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client                                       Server            │
│    │                                            │               │
│    │  POST /tasks                               │               │
│    │  Authorization: Bearer eyJ...              │               │
│    │  {"title": "My task"}                      │               │
│    ├───────────────────────────────────────────>│               │
│    │                                            │               │
│    │                          Validate token    │               │
│    │                          Get current user  │               │
│    │                          Create task with  │               │
│    │                          owner_id = user.id│               │
│    │                                            │               │
│    │  201 Created                               │               │
│    │  {"id": 1, "title": "My task", "owner_id": 1} │           │
│    │<───────────────────────────────────────────┤               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Hands-On Exercise

Build a complete authentication system with JWT:

**Step 1: Install dependencies**

```bash
cd my-api
uv add "python-jose[cryptography]"
```

**Step 2: Generate secret key**

```bash
openssl rand -hex 32
```

Copy the output.

**Step 3: Update `.env`**

```bash
# Add to existing .env
SECRET_KEY=<paste-your-generated-key-here>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Step 4: Update `config.py`**

```python
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Step 5: Create `auth.py`**

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from config import get_settings

settings = get_settings()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
```

**Step 6: Add login endpoint to `main.py`**

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from database import get_session
from models import User
from security import verify_password
from auth import create_access_token

app = FastAPI()

@app.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    statement = select(User).where(User.email == form_data.username)
    user = session.exec(statement).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
```

**Step 7: Add `get_current_user` dependency**

```python
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from auth import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()

    if user is None:
        raise credentials_exception

    return user
```

**Step 8: Add protected endpoint**

```python
@app.get("/users/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at
    }
```

**Step 9: Run the application**

```bash
uv run uvicorn main:app --reload
```

**Step 10: Test the complete flow**

```bash
# 1. Signup
curl -X POST http://localhost:8000/users/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass123"}'

# 2. Login
curl -X POST http://localhost:8000/token \
  -d "username=test@example.com" \
  -d "password=SecurePass123"

# Response: {"access_token": "eyJ...", "token_type": "bearer"}

# 3. Access protected route
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer eyJ..."

# Response: {"id": 1, "email": "test@example.com", "created_at": "..."}
```

**Step 11: Test with Swagger UI**

1. Go to http://localhost:8000/docs
2. Click "Authorize" button
3. Enter credentials:
   - username: `test@example.com`
   - password: `SecurePass123`
4. Click "Authorize"
5. Try `/users/me` endpoint - should work!
6. Click "Logout" to clear token
7. Try `/users/me` again - should fail with 401!

## Common Mistakes

**Mistake 1: Using JSON for `/token` endpoint**

```bash
# ❌ WRONG - OAuth2 expects form data, not JSON
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/json" \
  -d '{"username": "alice@example.com", "password": "pass"}'

# Error: 422 Unprocessable Entity

# ✅ CORRECT - Use form data
curl -X POST http://localhost:8000/token \
  -d "username=alice@example.com" \
  -d "password=pass"
```

**Why:** OAuth2 spec requires `application/x-www-form-urlencoded` for token endpoints.

**Mistake 2: Forgetting WWW-Authenticate header**

```python
# ❌ WRONG - Missing header
raise HTTPException(
    status_code=401,
    detail="Invalid credentials"
)

# ✅ CORRECT - Include WWW-Authenticate
raise HTTPException(
    status_code=401,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"}
)
```

**Why:** HTTP 401 responses should include WWW-Authenticate header to tell clients the auth method.

**Mistake 3: Putting sensitive data in tokens**

```python
# ❌ BAD - Token contains sensitive data
token = create_access_token({
    "sub": user.email,
    "password": user.hashed_password,  # Don't do this!
    "ssn": user.ssn  # Never do this!
})

# ✅ GOOD - Only user identifier
token = create_access_token({"sub": user.email})
```

**Why:** JWTs are signed, not encrypted. Anyone can decode and read the payload. Only include identifiers.

**Mistake 4: Hardcoding secret key**

```python
# ❌ BAD - Secret key in code
SECRET_KEY = "my-secret-key"

# ✅ GOOD - Secret key from environment
from config import get_settings
settings = get_settings()
# SECRET_KEY from .env file
```

**Mistake 5: Not checking token expiration**

```python
# ❌ BAD - Decode without validation
payload = jwt.decode(token, secret_key, algorithms=["HS256"], options={"verify_exp": False})

# ✅ GOOD - Expiration checked by default
payload = jwt.decode(token, secret_key, algorithms=["HS256"])
```

**Why:** Tokens should expire. Always validate expiration.

**Mistake 6: Revealing whether user exists**

```python
# ❌ BAD - Different messages reveal info
if not user:
    raise HTTPException(401, "User not found")
if not verify_password(password, user.hashed_password):
    raise HTTPException(401, "Wrong password")

# ✅ GOOD - Generic message
if not user or not verify_password(password, user.hashed_password):
    raise HTTPException(401, "Incorrect email or password")
```

**Why:** Prevents attackers from enumerating valid email addresses.

**Mistake 7: Not protecting routes**

```python
# ❌ BAD - Anyone can create tasks
@app.post("/tasks")
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    db_task = Task(**task.dict())
    session.add(db_task)
    session.commit()
    return db_task

# ✅ GOOD - Requires authentication
@app.post("/tasks")
def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    db_task = Task(**task.dict(), owner_id=current_user.id)
    session.add(db_task)
    session.commit()
    return db_task
```

## Key Points

- JWT provides stateless authentication (no session storage needed)
- JWTs are signed, not encrypted—anyone can read the payload
- Install with: `uv add "python-jose[cryptography]"`
- Generate secret key with: `openssl rand -hex 32`
- `/token` endpoint uses OAuth2PasswordRequestForm (form data, not JSON)
- OAuth2 uses `username` field for email (spec requirement)
- Use generic error messages to prevent user enumeration
- Include `WWW-Authenticate: Bearer` header in 401 responses
- `OAuth2PasswordBearer(tokenUrl="token")` extracts token from Authorization header
- `get_current_user` dependency validates token and returns User object
- Only include user identifier in token payload (e.g., `{"sub": email}`)
- Protect routes by adding `current_user: User = Depends(get_current_user)` parameter
- Associate resources with users via `owner_id` foreign key
- Check ownership before allowing updates/deletes (return 403 if not owned)
- Swagger UI has built-in OAuth2 support (Authorize button)
- Tokens expire automatically (default 30 minutes, configurable)

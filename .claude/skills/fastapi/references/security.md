# Security and Authentication Reference

Complete guide to implementing authentication, authorization, and security in FastAPI applications.

## Table of Contents
- Security Overview
- Password Hashing
- JWT Authentication
- OAuth2 with Password (and Bearer)
- OAuth2 with JWT Tokens
- API Key Authentication
- HTTP Basic Auth
- Security Best Practices

## Security Overview

FastAPI provides tools in `fastapi.security` for implementing security based on OpenAPI standards.

### Supported Security Schemes

1. **apiKey** - API key in query param, header, or cookie
2. **http** - HTTP authentication (Bearer, Basic, Digest)
3. **oauth2** - OAuth2 flows (password, implicit, clientCredentials, authorizationCode)
4. **openIdConnect** - OAuth2 with automatic discovery

## Password Hashing

Before implementing authentication, you must understand secure password storage. **Never store plaintext passwords.**

User passwords must be hashed before storage using Argon2:

```python
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

password_hash = PasswordHash((Argon2Hasher(),))

def hash_password(password: str) -> str:
    """Hash a password using Argon2."""
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return password_hash.verify(plain_password, hashed_password)
```

**Key principles:**

- Never store plaintext passwords
- Use Argon2 (gold standard, memory-hard, GPU-resistant)
- Never return password hashes in API responses
- Use `hashed_password` field name (not `password`)

**Installation:**

```bash
uv add "pwdlib[argon2]"
```

**See [references/user-management.md](user-management.md) for:**
- Complete password hashing guide
- Why Argon2 is the gold standard
- User signup implementation
- Security principles for password storage
- Hands-on exercises
- Common security mistakes

## JWT Authentication

Stateless authentication using signed tokens. Users log in once, receive a JWT, and include it in subsequent requests.

**How it works:**

1. User sends email/password to `/token`
2. Server verifies password and creates signed JWT
3. User includes token in `Authorization: Bearer <token>` header
4. Server validates signature and extracts user identity

**Key concepts:**

- JWTs are signed, not encrypted—anyone can read the payload
- Only include user identifiers in tokens (not sensitive data)
- Tokens expire automatically (configurable)
- OAuth2PasswordBearer extracts token from Authorization header
- OAuth2PasswordRequestForm expects form data (not JSON)

**Installation:**

```bash
uv add "python-jose[cryptography]"
```

**Generate secret key:**

```bash
openssl rand -hex 32
```

**See [references/jwt-authentication.md](jwt-authentication.md) for:**
- Complete JWT implementation guide
- Token creation and validation functions
- Login endpoint with OAuth2PasswordRequestForm
- Protected routes with get_current_user dependency
- Protecting resources with user ownership
- Swagger UI OAuth2 integration
- Complete authentication flow
- Common mistakes and best practices

## OAuth2 with Password and Bearer

### Basic OAuth2 Implementation

```python
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

app = FastAPI()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Fake user database
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    }
}

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

def fake_hash_password(password: str):
    return "fakehashed" + password

def fake_decode_token(token: str):
    # This is insecure - just for demonstration
    user = fake_users_db.get(token)
    if user:
        return UserInDB(**user)
    return None

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)

    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user
```

## OAuth2 with JWT Tokens (Production-Ready)

### Dependencies

```bash
pip install "python-jose[cryptography]" "passlib[bcrypt]"
```

### Complete JWT Implementation

```python
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = "your-secret-key-here-use-openssl-rand-hex-32"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

# Fake database
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "disabled": False,
    }
}

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Endpoints
@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user

@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return [{"item_id": "Foo", "owner": current_user.username}]
```

### Generate Secret Key

```bash
openssl rand -hex 32
```

## API Key Authentication

### Header-based API Key

```python
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY = "your-api-key-here"
api_key_header = APIKeyHeader(name="X-API-Key")

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key

@app.get("/protected")
async def protected_route(api_key: str = Depends(get_api_key)):
    return {"message": "Access granted"}
```

### Query Parameter API Key

```python
from fastapi.security import APIKeyQuery

api_key_query = APIKeyQuery(name="api_key")

async def get_api_key(api_key: str = Security(api_key_query)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key
```

### Cookie-based API Key

```python
from fastapi.security import APIKeyCookie

api_key_cookie = APIKeyCookie(name="session")

async def get_api_key(api_key: str = Security(api_key_cookie)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )
    return api_key
```

## HTTP Basic Auth

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = b"johndoe"
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = b"secret"
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/users/me")
def read_current_user(username: Annotated[str, Depends(get_current_username)]):
    return {"username": username}
```

## Security Best Practices

### 1. Never Store Plain Passwords

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash("my-password")

# Verify password
is_valid = pwd_context.verify("my-password", hashed)
```

### 2. Use Environment Variables for Secrets

```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
```

### 3. Use HTTPS in Production

Always use HTTPS for production APIs to protect tokens in transit.

### 4. Set Token Expiration

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Short-lived tokens
REFRESH_TOKEN_EXPIRE_DAYS = 7    # For refresh tokens
```

### 5. Validate All Inputs

```python
from pydantic import BaseModel, EmailStr, validator

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
```

### 6. Use Timing-Safe Comparison

```python
import secrets

# Instead of: if token == correct_token
# Use:
if secrets.compare_digest(token, correct_token):
    # Valid token
    pass
```

### 7. Implement Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/login")
@limiter.limit("5/minute")
async def login(request: Request):
    return {"message": "Login endpoint"}
```

### 8. OAuth2 Scopes for Permissions

```python
from fastapi import Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "items:read": "Read items",
        "items:write": "Write items",
        "users:read": "Read users"
    }
)

@app.get("/items/")
async def read_items(
    token: Annotated[str, Security(oauth2_scheme, scopes=["items:read"])]
):
    return [{"item": "Foo"}]
```

## Common Patterns

### Protected Route Dependency

```python
CurrentUser = Annotated[User, Depends(get_current_active_user)]

@app.get("/protected")
async def protected_route(current_user: CurrentUser):
    return {"user": current_user.username}
```

### Optional Authentication

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_current_user_optional(
    token: Annotated[str | None, Depends(oauth2_scheme)]
):
    if token is None:
        return None
    # Validate token and return user
    return user

@app.get("/items/")
async def read_items(current_user: Annotated[User | None, Depends(get_current_user_optional)]):
    if current_user:
        return {"message": f"Hello {current_user.username}"}
    return {"message": "Hello anonymous"}
```

### Role-based Access Control

```python
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"

def require_role(required_role: Role):
    async def role_checker(current_user: CurrentUser):
        if current_user.role != required_role and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: Annotated[User, Depends(require_role(Role.ADMIN))]
):
    return {"message": f"User {user_id} deleted"}
```

## Key Points

- Use OAuth2 with JWT for production APIs
- Never store plain passwords - always hash with bcrypt
- Use environment variables for secrets
- Implement token expiration
- Use HTTPS in production
- Validate all inputs with Pydantic
- Use timing-safe comparison for tokens
- Consider rate limiting for authentication endpoints
- OAuth2 scopes enable fine-grained permissions
- FastAPI's security utilities integrate with OpenAPI docs

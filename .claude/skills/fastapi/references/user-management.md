# User Management & Password Hashing Reference

Complete guide to implementing secure user management with password hashing in FastAPI. Learn why you never store passwords in plaintext and how to implement industry-standard security.

## Table of Contents
- Why Password Hashing Matters
- Installing Dependencies
- Password Hashing Functions
- User Model
- Signup Endpoint
- Security Principles Applied
- Hands-On Exercise
- Common Mistakes
- What's Next?

## Why Password Hashing Matters

**The Scenario: Your Database Leaks**

Databases get compromised. It's not "if," it's "when." What happens to your users' passwords?

**Plaintext Storage (❌ NEVER DO THIS):**

```python
# ❌ CATASTROPHICALLY BAD - Don't do this!
class User(SQLModel, table=True):
    email: str
    password: str  # Plaintext!

@app.post("/users/signup")
def signup(email: str, password: str, session: Session = Depends(get_session)):
    user = User(email=email, password=password)  # Storing plaintext!
    session.add(user)
    session.commit()
    return user
```

**Database contents:**

```
| email              | password      |
|--------------------|---------------|
| alice@example.com  | hunter2       |
| bob@example.com    | password123   |
| carol@example.com  | MySecret!     |
```

**If the database leaks:**

- Attacker gets all passwords instantly
- Users who reuse passwords across sites are now compromised everywhere
- No defense, no time to react
- Total catastrophic failure

**Hashed Storage (✅ CORRECT):**

```python
# ✅ SECURE - Hash passwords before storing
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

password_hash = PasswordHash((Argon2Hasher(),))

class User(SQLModel, table=True):
    email: str
    hashed_password: str  # Named explicitly

@app.post("/users/signup")
def signup(user: UserCreate, session: Session = Depends(get_session)):
    hashed = password_hash.hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed)
    session.add(db_user)
    session.commit()
    return {"id": db_user.id, "email": db_user.email}
```

**Database contents:**

```
| email              | hashed_password                                                   |
|--------------------|-------------------------------------------------------------------|
| alice@example.com  | $argon2id$v=19$m=65536,t=3,p=4$xYz...                            |
| bob@example.com    | $argon2id$v=19$m=65536,t=3,p=4$aBc...                            |
| carol@example.com  | $argon2id$v=19$m=65536,t=3,p=4$qWe...                            |
```

**If the database leaks:**

- Attacker gets useless hashes
- Each hash must be cracked individually (expensive!)
- Argon2 is memory-hard (resists GPU cracking)
- Users have time to change passwords
- Damage is minimized

**Why Argon2?**

Argon2 is the **gold standard** for password hashing:

- **Winner of the Password Hashing Competition (2015)**
- **Memory-hard** - Requires lots of RAM to compute, making GPU/ASIC attacks expensive
- **Resistant to side-channel attacks**
- **Configurable** - Can tune memory, iterations, parallelism
- **Modern** - Designed specifically for password hashing (not adapted from general hash functions)

**Comparison:**

| Algorithm | Status | Notes |
|-----------|--------|-------|
| **Argon2** | ✅ Use this | Gold standard, memory-hard, GPU-resistant |
| bcrypt | ⚠️ Acceptable | Older but still secure, less resistant to GPUs |
| PBKDF2 | ⚠️ Acceptable | Widely supported but less resistant to GPUs |
| MD5 | ❌ NEVER | Broken, fast to crack |
| SHA-1 | ❌ NEVER | Broken, fast to crack |
| SHA-256 (plain) | ❌ NEVER | Too fast, designed for different purpose |

**Key principle:** You never store passwords. You store _hashes_ of passwords. Hashing is one-way—you can't reverse it to get the original password.

## Installing Dependencies

Use `uv` to install `pwdlib` with Argon2 support:

```bash
uv add "pwdlib[argon2]"
```

**What gets installed:**

- `pwdlib` - Modern password hashing library for Python
- `argon2-cffi` - Argon2 implementation (via `[argon2]` extra)

**Why pwdlib?**

- Modern, actively maintained
- Simple API (`hash()`, `verify()`)
- Supports multiple hashers (Argon2, bcrypt, scrypt)
- Type-safe with good defaults

**Alternative (older approach):**

```bash
# You might see this in older tutorials - still works but less modern
uv add passlib bcrypt
```

We use `pwdlib` because it's newer, simpler, and follows modern best practices.

## Password Hashing Functions

Create a `security.py` module with password hashing utilities:

**security.py:**

```python
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# Create password hasher with Argon2
password_hash = PasswordHash((Argon2Hasher(),))

def hash_password(password: str) -> str:
    """
    Hash a plaintext password using Argon2.

    Args:
        password: Plaintext password to hash

    Returns:
        Hashed password string (safe to store in database)

    Example:
        >>> hash_password("MySecret123")
        "$argon2id$v=19$m=65536,t=3,p=4$..."
    """
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a hashed password.

    Args:
        plain_password: Plaintext password from user
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("MySecret123")
        >>> verify_password("MySecret123", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    return password_hash.verify(plain_password, hashed_password)
```

**Usage:**

```python
from security import hash_password, verify_password

# Signup: hash the password
password = "MySecret123"
hashed = hash_password(password)
print(hashed)
# $argon2id$v=19$m=65536,t=3,p=4$xYzAbC...

# Login: verify the password
if verify_password("MySecret123", hashed):
    print("Password correct!")
else:
    print("Password wrong!")
```

**Important notes:**

- `hash_password()` generates a **different hash every time** (includes random salt)
- This is intentional and secure—prevents rainbow table attacks
- `verify_password()` knows how to extract the salt and verify correctly

**Example:**

```python
hash1 = hash_password("password123")
hash2 = hash_password("password123")

print(hash1 == hash2)  # False - Different hashes!

# But both verify correctly:
print(verify_password("password123", hash1))  # True
print(verify_password("password123", hash2))  # True
```

## User Model

Define SQLModel models for user management:

**models.py:**

```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import EmailStr

class User(SQLModel, table=True):
    """Database model for users."""
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str  # Note: "hashed_password", not "password"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(SQLModel):
    """Request model for user signup."""
    email: EmailStr
    password: str = Field(min_length=8)

class UserResponse(SQLModel):
    """Response model for user endpoints (excludes password)."""
    id: int
    email: EmailStr
    created_at: datetime
```

**Key design decisions:**

1. **`hashed_password` field name**
   - Makes it clear this is NOT plaintext
   - Prevents accidental plaintext storage
   - Self-documenting code

2. **`email` is unique and indexed**
   - `unique=True` - Database enforces uniqueness
   - `index=True` - Fast lookups for login
   - Prevents duplicate accounts

3. **`EmailStr` type**
   - Validates email format automatically
   - Requires `email-validator`: `uv add email-validator`
   - FastAPI validates before endpoint runs

4. **Separate request/response models**
   - `UserCreate` - Accepts `password` (plaintext)
   - `User` - Stores `hashed_password`
   - `UserResponse` - Returns safe fields only (no hash!)

5. **`password` field has `min_length=8`**
   - Basic security requirement
   - Prevents weak passwords
   - Can add more validation (uppercase, numbers, etc.)

**Why separate models?**

```python
# ❌ BAD - Single model exposes hash
class User(SQLModel, table=True):
    email: str
    hashed_password: str

@app.post("/users/signup")
def signup(user: User, session: Session = Depends(get_session)):
    session.add(user)
    session.commit()
    return user  # ⚠️ Returns hashed_password to client!

# ✅ GOOD - Separate models, safe response
class User(SQLModel, table=True):
    email: EmailStr
    hashed_password: str

class UserCreate(SQLModel):
    email: EmailStr
    password: str

class UserResponse(SQLModel):
    id: int
    email: EmailStr

@app.post("/users/signup", response_model=UserResponse)
def signup(user: UserCreate, session: Session = Depends(get_session)):
    db_user = User(email=user.email, hashed_password=hash_password(user.password))
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user  # FastAPI uses UserResponse, excludes hash
```

## Signup Endpoint

Implement user registration with password hashing and duplicate prevention:

**main.py:**

```python
from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import Session, select
from database import get_session
from models import User, UserCreate, UserResponse
from security import hash_password

app = FastAPI()

@app.post("/users/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate, session: Session = Depends(get_session)):
    """
    Register a new user.

    Steps:
    1. Check if email already exists
    2. Hash the password
    3. Create user in database
    4. Return safe user data (no password hash)
    """
    # Step 1: Check for duplicate email
    statement = select(User).where(User.email == user.email)
    existing_user = session.exec(statement).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Step 2: Hash the password
    hashed = hash_password(user.password)

    # Step 3: Create user
    db_user = User(
        email=user.email,
        hashed_password=hashed
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    # Step 4: Return safe data (response_model excludes hash)
    return db_user
```

**Request:**

```bash
curl -X POST http://localhost:8000/users/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "MySecurePassword123"
  }'
```

**Response:**

```json
{
  "id": 1,
  "email": "alice@example.com",
  "created_at": "2024-01-15T10:30:00"
}
```

**Database record:**

```sql
SELECT * FROM user WHERE email = 'alice@example.com';

id | email              | hashed_password                                    | created_at
---|--------------------|---------------------------------------------------|-------------------
1  | alice@example.com  | $argon2id$v=19$m=65536,t=3,p=4$xYzAbC...        | 2024-01-15 10:30:00
```

**Error cases:**

**1. Duplicate email:**

```bash
# Try to register again with same email
curl -X POST http://localhost:8000/users/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "DifferentPassword"
  }'
```

**Response:**

```json
{
  "detail": "Email already registered"
}
```

**2. Invalid email format:**

```bash
curl -X POST http://localhost:8000/users/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "not-an-email",
    "password": "MyPassword123"
  }'
```

**Response:**

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address"
    }
  ]
}
```

**3. Password too short:**

```bash
curl -X POST http://localhost:8000/users/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@example.com",
    "password": "short"
  }'
```

**Response:**

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters"
    }
  ]
}
```

## Security Principles Applied

This implementation follows critical security principles:

### 1. Never Store Plaintext Passwords

```python
# ❌ BAD
user.password = "MySecret123"

# ✅ GOOD
user.hashed_password = hash_password("MySecret123")
```

**Why:** If database leaks, plaintext passwords expose all user accounts immediately.

### 2. Never Return Hashes in Responses

```python
# ❌ BAD
return user  # Includes hashed_password field

# ✅ GOOD
return UserResponse(id=user.id, email=user.email, created_at=user.created_at)
```

**Why:** While hashes are better than plaintext, they shouldn't be exposed. Defense in depth.

### 3. Prevent Email Enumeration (Carefully)

```python
# ❌ BAD - Reveals which emails are registered
if existing_user:
    raise HTTPException(400, "This email is already registered")
else:
    raise HTTPException(400, "Invalid credentials")

# ⚠️ TRADEOFF - Clear message vs enumeration
if existing_user:
    raise HTTPException(400, "Email already registered")
```

**Tradeoff:** Signup endpoints usually tell you if email exists (better UX). Login endpoints should NOT reveal this (security). Choose based on endpoint type.

### 4. Use Modern Algorithms

```python
# ❌ BAD - Weak algorithms
import hashlib
hash = hashlib.md5(password.encode()).hexdigest()

# ✅ GOOD - Argon2
from pwdlib.hashers.argon2 import Argon2Hasher
password_hash = PasswordHash((Argon2Hasher(),))
```

**Why:** MD5/SHA are designed for speed, not security. Argon2 is designed specifically for passwords (slow, memory-hard).

### 5. Name Fields Explicitly

```python
# ❌ CONFUSING - Is this plaintext or hashed?
class User(SQLModel, table=True):
    password: str

# ✅ CLEAR - Obviously hashed
class User(SQLModel, table=True):
    hashed_password: str
```

**Why:** Explicit naming prevents accidental plaintext storage.

### 6. Validate Email Format

```python
# ❌ BAD - No validation
email: str

# ✅ GOOD - Validates email format
from pydantic import EmailStr
email: EmailStr
```

**Why:** Prevents garbage data, ensures emails are valid for sending.

### 7. Enforce Password Strength

```python
# ❌ BAD - No requirements
password: str

# ✅ GOOD - Minimum length
password: str = Field(min_length=8)

# ✅ BETTER - More requirements (example)
from pydantic import field_validator

class UserCreate(SQLModel):
    password: str = Field(min_length=8)

    @field_validator("password")
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v
```

**Why:** Prevents weak passwords that are easy to guess or crack.

## Hands-On Exercise

Build a complete user management system with secure password hashing:

**Step 1: Install dependencies**

```bash
cd my-api
uv add "pwdlib[argon2]" email-validator
```

**Step 2: Create `security.py`**

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

**Step 3: Update `models.py`**

```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import EmailStr

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(SQLModel):
    email: EmailStr
    password: str = Field(min_length=8)

class UserResponse(SQLModel):
    id: int
    email: EmailStr
    created_at: datetime
```

**Step 4: Add signup endpoint to `main.py`**

```python
from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import Session, select
from database import get_session
from models import User, UserCreate, UserResponse
from security import hash_password

app = FastAPI()

@app.post("/users/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate, session: Session = Depends(get_session)):
    # Check for duplicate email
    statement = select(User).where(User.email == user.email)
    existing_user = session.exec(statement).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password and create user
    hashed = hash_password(user.password)
    db_user = User(email=user.email, hashed_password=hashed)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user
```

**Step 5: Update database startup in `main.py`**

```python
from sqlmodel import SQLModel
from database import engine
import models  # Import so SQLModel knows about User model

@app.on_event("startup")
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
```

**Step 6: Run the application**

```bash
uv run uvicorn main:app --reload
```

**Step 7: Test signup flow**

```bash
# Create a user
curl -X POST http://localhost:8000/users/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123"
  }'

# Response:
# {
#   "id": 1,
#   "email": "test@example.com",
#   "created_at": "2024-01-15T10:30:00"
# }

# Try duplicate (should fail)
curl -X POST http://localhost:8000/users/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "DifferentPassword"
  }'

# Response:
# {
#   "detail": "Email already registered"
# }
```

**Step 8: Verify hashes in database**

Using Neon SQL Editor or local psql:

```sql
SELECT * FROM user;
```

**Output:**

```
id | email              | hashed_password                                    | created_at
---|--------------------|---------------------------------------------------|-------------------
1  | test@example.com   | $argon2id$v=19$m=65536,t=3,p=4$xYz...           | 2024-01-15 10:30:00
```

**Step 9: Test password verification**

Create a test script:

```python
# test_security.py
from security import hash_password, verify_password

# Hash a password
password = "SecurePass123"
hashed = hash_password(password)
print(f"Hashed: {hashed}")

# Verify correct password
if verify_password("SecurePass123", hashed):
    print("✅ Correct password verified")

# Verify wrong password
if not verify_password("WrongPassword", hashed):
    print("✅ Wrong password rejected")

# Show that hashes are different each time
hash1 = hash_password("password123")
hash2 = hash_password("password123")
print(f"\nHash 1: {hash1}")
print(f"Hash 2: {hash2}")
print(f"Same? {hash1 == hash2}")  # False - but both verify!
```

Run:

```bash
uv run python test_security.py
```

## Common Mistakes

**Mistake 1: Storing plaintext passwords**

```python
# ❌ CATASTROPHICALLY BAD
class User(SQLModel, table=True):
    email: str
    password: str  # PLAINTEXT!

@app.post("/signup")
def signup(email: str, password: str, session: Session = Depends(get_session)):
    user = User(email=email, password=password)  # Storing plaintext!
    session.add(user)
    session.commit()
    return user
```

**Why it's bad:** Total security failure. If database leaks, all passwords exposed.

**Fix:**

```python
# ✅ CORRECT
class User(SQLModel, table=True):
    email: str
    hashed_password: str

@app.post("/signup")
def signup(user: UserCreate, session: Session = Depends(get_session)):
    hashed = hash_password(user.password)
    db_user = User(email=user.email, hashed_password=hashed)
    session.add(db_user)
    session.commit()
    return db_user
```

**Mistake 2: Returning hash in response**

```python
# ❌ BAD - Exposes hash
@app.post("/signup")
def signup(user: UserCreate, session: Session = Depends(get_session)):
    hashed = hash_password(user.password)
    db_user = User(email=user.email, hashed_password=hashed)
    session.add(db_user)
    session.commit()
    return db_user  # Includes hashed_password!
```

**Fix:**

```python
# ✅ CORRECT - Use response_model
@app.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, session: Session = Depends(get_session)):
    hashed = hash_password(user.password)
    db_user = User(email=user.email, hashed_password=hashed)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user  # FastAPI uses UserResponse, excludes hash
```

**Mistake 3: Using weak hashing algorithms**

```python
# ❌ BAD - MD5 is broken
import hashlib
hash = hashlib.md5(password.encode()).hexdigest()

# ❌ BAD - SHA-256 is too fast
import hashlib
hash = hashlib.sha256(password.encode()).hexdigest()

# ✅ CORRECT - Argon2
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
password_hash = PasswordHash((Argon2Hasher(),))
hash = password_hash.hash(password)
```

**Mistake 4: Naming field `password` instead of `hashed_password`**

```python
# ❌ CONFUSING - Ambiguous
class User(SQLModel, table=True):
    email: str
    password: str  # Is this plaintext or hashed?

# ✅ CLEAR - Explicit
class User(SQLModel, table=True):
    email: str
    hashed_password: str  # Obviously hashed
```

**Mistake 5: Not checking for duplicate emails**

```python
# ❌ BAD - Allows duplicates (will crash on unique constraint)
@app.post("/signup")
def signup(user: UserCreate, session: Session = Depends(get_session)):
    hashed = hash_password(user.password)
    db_user = User(email=user.email, hashed_password=hashed)
    session.add(db_user)
    session.commit()  # May crash with "duplicate key" error
    return db_user

# ✅ CORRECT - Check first
@app.post("/signup")
def signup(user: UserCreate, session: Session = Depends(get_session)):
    # Check for duplicate
    existing = session.exec(select(User).where(User.email == user.email)).first()
    if existing:
        raise HTTPException(400, "Email already registered")

    hashed = hash_password(user.password)
    db_user = User(email=user.email, hashed_password=hashed)
    session.add(db_user)
    session.commit()
    return db_user
```

**Mistake 6: Not validating password strength**

```python
# ❌ BAD - Accepts weak passwords
class UserCreate(SQLModel):
    email: EmailStr
    password: str  # No validation

# ✅ GOOD - Minimum length
class UserCreate(SQLModel):
    email: EmailStr
    password: str = Field(min_length=8)

# ✅ BETTER - Additional validation
from pydantic import field_validator

class UserCreate(SQLModel):
    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("password")
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Must contain uppercase")
        if not any(c.isdigit() for c in v):
            raise ValueError("Must contain digit")
        return v
```

**Mistake 7: Not indexing email field**

```python
# ❌ BAD - Slow lookups
class User(SQLModel, table=True):
    email: str = Field(unique=True)  # Unique but not indexed

# ✅ GOOD - Fast lookups
class User(SQLModel, table=True):
    email: str = Field(unique=True, index=True)
```

**Why:** Login will query by email frequently. Index makes it fast.

## What's Next: JWT Authentication

You've implemented secure user signup with password hashing. Now users can register, but they can't log in yet!

**The next step is JWT Authentication:**

- Login endpoint that verifies email/password
- JWT token generation with signed claims
- Protected routes requiring valid tokens
- Get current user from token
- Associate resources with users

**Quick preview:**

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from datetime import datetime, timedelta

# Login endpoint
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Find user and verify password
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password")

    # Create JWT token
    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# Protected route
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/users/me")
def read_current_user(token: str = Depends(oauth2_scheme)):
    # Validate token and get user
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    email = payload.get("sub")
    user = session.exec(select(User).where(User.email == email)).first()
    return user
```

**See [references/jwt-authentication.md](jwt-authentication.md) for:**
- Complete JWT implementation guide
- How JWT works (stateless, signed tokens)
- Token creation and validation functions
- Login endpoint with OAuth2PasswordRequestForm
- Protected routes with get_current_user dependency
- Protecting task routes with user ownership
- Swagger UI OAuth2 integration
- Complete authentication flow diagram
- Hands-on exercises
- Common mistakes and best practices

## Key Points

- Never store plaintext passwords—always hash them
- Argon2 is the gold standard for password hashing (memory-hard, GPU-resistant)
- Install with: `uv add "pwdlib[argon2]"`
- Use `hashed_password` field name (not `password`) to prevent confusion
- Never return password hashes in API responses
- Check for duplicate emails before creating users
- Use `EmailStr` for automatic email validation
- Enforce minimum password length (8+ characters)
- Index the email field for fast lookups
- Separate request/response models (UserCreate, User, UserResponse)
- Each hash is unique even for same password (includes random salt)
- Password hashing is one-way—you can't reverse it

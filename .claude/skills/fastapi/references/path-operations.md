# Path Operations Reference

Complete guide to handling path operations, parameters, request bodies, and responses in FastAPI.

**See [references/crud-operations.md](references/crud-operations.md) for:**
- Complete CRUD implementation guide
- HTTP method semantics and idempotency
- Filtering and query parameters
- Update complexity (PUT vs PATCH)
- Complete Task API example
- Hands-on exercises and challenges

**See [references/error-handling.md](references/error-handling.md) for:**
- Complete guide to HTTPException
- 400 vs 422 distinction with examples
- Error message design
- Status code semantics
- Agent-friendly error responses

## Table of Contents
- HTTP Methods and Decorators
- Path Parameters
- Query Parameters
- Request Body
- Response Models
- Multiple Parameters
- Data Validation

## HTTP Methods and Decorators

FastAPI provides decorators for all HTTP methods:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/")        # Read
async def read_items():
    pass

@app.post("/items/")       # Create
async def create_item():
    pass

@app.put("/items/{id}")    # Update (full)
async def update_item(id: int):
    pass

@app.patch("/items/{id}")  # Update (partial)
async def patch_item(id: int):
    pass

@app.delete("/items/{id}") # Delete
async def delete_item(id: int):
    pass
```

## Path Parameters

### Basic Path Parameters with Type Hints

```python
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

**Benefits:**
- Automatic parsing (string → int)
- Data validation
- Editor support
- Auto-documentation

### Predefined Values with Enums

```python
from enum import Enum

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}
    return {"model_name": model_name, "message": "Have some residuals"}
```

### Path Parameters with File Paths

Use `:path` converter for paths containing slashes:

```python
@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}
```

**Example:** `/files/home/user/file.txt` → `{"file_path": "home/user/file.txt"}`

### Route Order Matters

Fixed paths must be declared **before** parameterized paths:

```python
@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}

@app.get("/users/{user_id}")  # Declare AFTER fixed paths
async def read_user(user_id: str):
    return {"user_id": user_id}
```

## Query Parameters

Query parameters are function parameters not in the path.

### Basic Query Parameters

```python
@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]
```

**URL:** `http://localhost:8000/items/?skip=20&limit=10`

### Optional Query Parameters

```python
@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str | None = None):
    if q:
        return {"item_id": item_id, "q": q}
    return {"item_id": item_id}
```

### Boolean Query Parameters

```python
@app.get("/items/{item_id}")
async def read_item(item_id: str, short: bool = False):
    item = {"item_id": item_id}
    if not short:
        item.update({"description": "Long description here"})
    return item
```

**Bool conversion:** `?short=1`, `?short=True`, `?short=yes`, `?short=on` → `True`

### Required Query Parameters

Omit default value to make required:

```python
@app.get("/items/{item_id}")
async def read_item(item_id: str, needy: str):  # needy is required
    return {"item_id": item_id, "needy": needy}
```

### Multiple Parameter Types

```python
@app.get("/items/{item_id}")
async def read_item(
    item_id: str,              # required path parameter
    needy: str,                # required query parameter
    skip: int = 0,             # optional with default
    limit: int | None = None   # optional, no default
):
    return {"item_id": item_id, "needy": needy, "skip": skip, "limit": limit}
```

## Why Pydantic Matters for Agents

GET endpoints retrieve data. POST endpoints create data. To create a task, you need to send data in the request body. FastAPI uses Pydantic models to define what that data should look like and validate it automatically.

This matters for agents: when clients send requests to your agent endpoints, Pydantic ensures the input is valid _before_ your agent sees it. Bad data gets rejected at the door, not halfway through an expensive LLM call.

In MCP servers, you validated tool parameters. Pydantic does the same thing for HTTP APIs. When an agent endpoint receives JSON, Pydantic:

1. Parses the raw JSON bytes
2. Validates data types match your model
3. Checks required fields are present
4. Rejects invalid data with helpful error messages

This validation layer is critical when agents compose tools. One agent's output becomes another's input. Type safety at every boundary prevents cascading failures.

## How Pydantic Validates (Under the Hood)

When you write `title: str`, Pydantic:

1. **Checks existence** — Is there a "title" key in the JSON? Missing → `Field required` error
2. **Checks type** — Is the value a string? Wrong type → `string_type` error
3. **Attempts coercion** — `"123"` (string) passes. `123` (int) gets coerced to `"123"`
4. **Passes validated data** — Your function receives a guaranteed string

This is why `task.title` in your function is GUARANTEED to be a string. No defensive `if isinstance(title, str)` checks needed.

But what if you need custom validation? Title must be 3-100 characters:

```python
from pydantic import BaseModel, Field

class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    description: str | None = None
```

Now Pydantic enforces length constraints automatically.

## Request Body

Use Pydantic models for request bodies.

### Basic Request Body

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

@app.post("/items/")
async def create_item(item: Item):
    return item
```

**Request:**
```json
{
    "name": "Foo",
    "description": "An optional description",
    "price": 45.2,
    "tax": 3.5
}
```

### Using Model Data

```python
@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.model_dump()
    if item.tax is not None:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict
```

### Defining Task Models

Separating request and response models is a best practice:

* Client says: "Create a task with this title"
* Server says: "Here's your task with ID 1, status pending"

This separation matters more as your API grows. You might have `TaskCreate`, `TaskUpdate`, `TaskResponse`, `TaskSummary`—each exposing exactly what that operation needs.

```python
from pydantic import BaseModel

# Request model - what client sends
class TaskCreate(BaseModel):
    title: str
    description: str | None = None

# Response model - what API returns
class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: str

# In-memory storage
tasks: list[dict] = []

@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate):
    new_task = {
        "id": len(tasks) + 1,
        "title": task.title,
        "description": task.description,
        "status": "pending"
    }
    tasks.append(new_task)
    return new_task
```

**Breaking down the key elements:**

* `@app.post("/tasks")` — This endpoint handles POST requests
* `task: TaskCreate` — FastAPI parses the request body as a `TaskCreate` model
* `response_model=TaskResponse` — FastAPI validates the response matches this model
* `status_code=201` — Return 201 Created instead of default 200

### Request Body + Path Parameters

```python
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.model_dump()}
```

### Request Body + Path + Query Parameters

```python
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, q: str | None = None):
    result = {"item_id": item_id, **item.model_dump()}
    if q:
        result.update({"q": q})
    return result
```

**Parameter Recognition:**
- **Path**: Declared in route (e.g., `{item_id}`)
- **Query**: Singular types with defaults (e.g., `str | None = None`)
- **Body**: Pydantic model parameters

## Response Models

### Basic Response Model

```python
from pydantic import BaseModel

class ItemOut(BaseModel):
    name: str
    price: float

@app.post("/items/", response_model=ItemOut)
async def create_item(item: Item):
    return item  # Only name and price returned
```

### Multiple Response Models

```python
from typing import Union

class UserIn(BaseModel):
    username: str
    password: str
    email: str

class UserOut(BaseModel):
    username: str
    email: str

@app.post("/users/", response_model=UserOut)
async def create_user(user: UserIn):
    return user  # Password automatically excluded
```

### Response Status Codes

```python
from fastapi import status

@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item):
    return item

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    return None
```

## Validation Errors: What Students Find Confusing

This is where many students get stuck. Let's work through it carefully.

**Try posting with missing title:**

```json
{
  "description": "Missing title"
}
```

**Output:**

```json
HTTP/1.1 422 Unprocessable Entity
content-type: application/json

{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "title"],
      "msg": "Field required",
      "input": {"description": "Missing title"}
    }
  ]
}
```

**Reading this error:**

* `type: "missing"` — What kind of validation failure
* `loc: ["body", "title"]` — Where the error is: in the body, at field "title"
* `msg: "Field required"` — Human-readable explanation
* `input` — What you actually sent

**Why 422 and not 400?**

This confuses people. Here's the distinction:

* **422 Unprocessable Entity** — The JSON is valid, but data doesn't match the schema. Pydantic catches these automatically.
* **400 Bad Request** — Business logic validation failed (e.g., "title can't be empty whitespace" after trimming). You handle these in your code with `HTTPException`.

FastAPI automatically returns 422 for schema violations. You'll add 400 errors in error handling lessons.

**Try posting with wrong type:**

```json
{
  "title": 123
}
```

**Output:**

```json
HTTP/1.1 422 Unprocessable Entity
content-type: application/json

{
  "detail": [
    {
      "type": "string_type",
      "loc": ["body", "title"],
      "msg": "Input should be a valid string",
      "input": 123
    }
  ]
}
```

Pydantic caught that `title` should be a string, not a number.

## Data Validation

FastAPI/Pydantic provides automatic validation:

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(None, max_length=300)
    price: float = Field(..., gt=0)  # Greater than 0
    tax: float | None = Field(None, ge=0)  # Greater or equal to 0

@app.post("/items/")
async def create_item(item: Item):
    return item
```

**Validation features:**
- String length: `min_length`, `max_length`
- Numeric: `gt`, `ge`, `lt`, `le`
- Regex patterns: `pattern`
- Custom validators

## Advanced Request Body

### Nested Models

```python
from pydantic import BaseModel

class Image(BaseModel):
    url: str
    name: str

class Item(BaseModel):
    name: str
    images: list[Image] | None = None

@app.post("/items/")
async def create_item(item: Item):
    return item
```

### List Bodies

```python
@app.post("/images/")
async def create_images(images: list[Image]):
    return images
```

### Arbitrary dict Bodies

```python
@app.post("/index-weights/")
async def create_weights(weights: dict[int, float]):
    return weights
```

## Key Points

- Use type hints for automatic validation and documentation
- Order matters: declare fixed paths before parameterized ones
- Pydantic models enable request/response validation
- FastAPI automatically distinguishes path, query, and body parameters
- All validations appear in OpenAPI docs automatically

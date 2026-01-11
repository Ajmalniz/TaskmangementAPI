# Background Tasks Reference

Complete guide to implementing background tasks in FastAPI for operations that run after returning responses.

## Table of Contents
- What are Background Tasks
- Basic Usage
- With Dependencies
- Multiple Background Tasks
- Task Parameters
- When to Use Background Tasks
- Alternative Solutions

## What are Background Tasks

Background tasks run **after** the response has been sent to the client. They're useful for operations where the client doesn't need to wait.

### Common Use Cases

- **Email notifications**: Send emails without delaying responses
- **Data processing**: Process uploaded files asynchronously
- **Logging**: Write detailed logs after response
- **Webhooks**: Notify external services
- **Cache updates**: Refresh cached data
- **Cleanup**: Delete temporary files

### What Background Tasks Are NOT

- **Not for heavy computation**: Use Celery/RQ for CPU-intensive tasks
- **Not for long-running tasks**: Limited to request lifetime
- **Not distributed**: Runs in the same process
- **Not persistent**: Lost if server restarts

## Basic Usage

### Import and Add Task

```python
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

def write_notification(email: str, message: str = ""):
    with open("log.txt", mode="a") as log:
        content = f"notification for {email}: {message}\n"
        log.write(content)

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_notification, email, message="some notification")
    return {"message": "Notification sent in the background"}
```

**Flow:**
1. Response returns immediately
2. `write_notification` runs after response is sent
3. Client doesn't wait for the task to complete

### Task Function Requirements

Background task functions can be:
- Regular functions (`def`)
- Async functions (`async def`)

FastAPI handles both automatically.

```python
# Sync function
def sync_task(param: str):
    # Blocking operations
    time.sleep(1)
    print(f"Sync task: {param}")

# Async function
async def async_task(param: str):
    # Can use await
    await asyncio.sleep(1)
    print(f"Async task: {param}")

@app.post("/tasks")
async def create_task(background_tasks: BackgroundTasks):
    background_tasks.add_task(sync_task, "test1")
    background_tasks.add_task(async_task, "test2")
    return {"status": "tasks queued"}
```

## With Dependencies

Background tasks work with FastAPI's dependency injection:

```python
from typing import Annotated
from fastapi import BackgroundTasks, Depends

def write_log(message: str):
    with open("log.txt", mode="a") as log:
        log.write(message + "\n")

def get_query(background_tasks: BackgroundTasks, q: str | None = None):
    if q:
        message = f"found query: {q}"
        background_tasks.add_task(write_log, message)
    return q

@app.post("/send-notification/{email}")
async def send_notification(
    email: str,
    background_tasks: BackgroundTasks,
    q: Annotated[str, Depends(get_query)]
):
    # Add task from path operation
    background_tasks.add_task(write_log, f"message to {email}")
    return {"message": "Message sent"}
```

**Task execution:**
- Tasks from dependencies run first
- Tasks from path operation run second
- All tasks execute in the order they were added

## Multiple Background Tasks

Add multiple tasks to run sequentially:

```python
def task_1(name: str):
    print(f"Task 1: {name}")

def task_2(name: str):
    print(f"Task 2: {name}")

def task_3(name: str):
    print(f"Task 3: {name}")

@app.post("/multiple-tasks")
async def multiple_tasks(background_tasks: BackgroundTasks):
    background_tasks.add_task(task_1, "First")
    background_tasks.add_task(task_2, "Second")
    background_tasks.add_task(task_3, "Third")
    return {"status": "3 tasks queued"}
```

**Execution order:** task_1 → task_2 → task_3

## Task Parameters

### Positional and Keyword Arguments

```python
def complex_task(arg1: str, arg2: int, kwarg1: str = "default", kwarg2: bool = False):
    print(f"Args: {arg1}, {arg2}")
    print(f"Kwargs: {kwarg1}, {kwarg2}")

@app.post("/complex")
async def complex_endpoint(background_tasks: BackgroundTasks):
    # With positional arguments
    background_tasks.add_task(complex_task, "hello", 42, kwarg1="world", kwarg2=True)
    return {"status": "task queued"}
```

### Passing Objects

```python
from pydantic import BaseModel

class EmailData(BaseModel):
    recipient: str
    subject: str
    body: str

def send_email(email_data: EmailData):
    # Send email using email_data
    print(f"Sending to {email_data.recipient}: {email_data.subject}")

@app.post("/send-email")
async def send_email_endpoint(email_data: EmailData, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, email_data)
    return {"status": "email queued"}
```

## Common Patterns

### Email Notifications

```python
from pydantic import EmailStr

def send_email_notification(email: EmailStr, subject: str, message: str):
    # Email sending logic
    print(f"Sending email to {email}")
    print(f"Subject: {subject}")
    print(f"Message: {message}")
    # Use SMTP or email service API

@app.post("/register")
async def register_user(
    email: EmailStr,
    password: str,
    background_tasks: BackgroundTasks
):
    # Create user account
    user = create_user(email, password)

    # Send welcome email in background
    background_tasks.add_task(
        send_email_notification,
        email,
        "Welcome!",
        f"Welcome to our service, {email}!"
    )

    return {"user_id": user.id, "email": user.email}
```

### File Processing

```python
from fastapi import File, UploadFile
import shutil

def process_uploaded_file(file_path: str):
    # Process the file
    print(f"Processing {file_path}")
    # Image processing, data parsing, etc.

@app.post("/upload")
async def upload_file(
    file: UploadFile,
    background_tasks: BackgroundTasks
):
    # Save file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process in background
    background_tasks.add_task(process_uploaded_file, file_path)

    return {"filename": file.filename, "status": "uploaded, processing"}
```

### Webhook Notifications

```python
import httpx

async def send_webhook(url: str, data: dict):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data)
            print(f"Webhook sent: {response.status_code}")
        except Exception as e:
            print(f"Webhook failed: {e}")

@app.post("/orders")
async def create_order(
    order_data: dict,
    background_tasks: BackgroundTasks
):
    # Create order
    order = create_order_in_db(order_data)

    # Notify external system
    background_tasks.add_task(
        send_webhook,
        "https://example.com/webhook",
        {"order_id": order.id, "status": "created"}
    )

    return order
```

### Database Cleanup

```python
def cleanup_old_records(days: int = 30):
    # Delete old records from database
    cutoff_date = datetime.now() - timedelta(days=days)
    # db.query(OldModel).filter(OldModel.created_at < cutoff_date).delete()
    print(f"Cleaned records older than {days} days")

@app.post("/cleanup")
async def trigger_cleanup(background_tasks: BackgroundTasks):
    background_tasks.add_task(cleanup_old_records, days=30)
    return {"status": "cleanup scheduled"}
```

### Audit Logging

```python
def log_user_action(user_id: int, action: str, details: dict):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "action": action,
        "details": details
    }
    # Write to audit log database or file
    print(f"Audit log: {log_entry}")

@app.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    current_user: User,
    background_tasks: BackgroundTasks
):
    # Delete item
    deleted_item = delete_item_from_db(item_id)

    # Log action
    background_tasks.add_task(
        log_user_action,
        current_user.id,
        "delete_item",
        {"item_id": item_id, "item_name": deleted_item.name}
    )

    return {"status": "deleted"}
```

### Cache Invalidation

```python
async def invalidate_cache(cache_key: str):
    # Invalidate cache entry
    await redis_client.delete(cache_key)
    print(f"Cache invalidated: {cache_key}")

@app.put("/items/{item_id}")
async def update_item(
    item_id: int,
    item_data: dict,
    background_tasks: BackgroundTasks
):
    # Update item
    updated_item = update_item_in_db(item_id, item_data)

    # Invalidate cache
    background_tasks.add_task(invalidate_cache, f"item:{item_id}")
    background_tasks.add_task(invalidate_cache, "items:list")

    return updated_item
```

## Error Handling in Background Tasks

```python
import logging

logger = logging.getLogger(__name__)

def risky_task(param: str):
    try:
        # Task logic that might fail
        if param == "fail":
            raise ValueError("Task failed")
        print(f"Task succeeded: {param}")
    except Exception as e:
        logger.error(f"Background task error: {e}")
        # Handle error (retry, alert, etc.)

@app.post("/risky")
async def risky_endpoint(param: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(risky_task, param)
    return {"status": "task queued"}
```

## Limitations and Alternatives

### When NOT to Use Background Tasks

1. **Heavy CPU-intensive tasks** → Use Celery or RQ
2. **Tasks that outlive request** → Use task queues
3. **Distributed systems** → Use message queues (RabbitMQ, Kafka)
4. **Persistent task tracking** → Use Celery with result backend
5. **Scheduled/periodic tasks** → Use Celery Beat or APScheduler

### Alternative: Celery

**For production-grade task processing:**

```python
from celery import Celery

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task
def heavy_computation(data):
    # Long-running task
    return result

@app.post("/compute")
async def compute(data: dict):
    # Queue task in Celery
    task = heavy_computation.delay(data)
    return {"task_id": task.id}
```

### Alternative: APScheduler

**For scheduled tasks:**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

def scheduled_task():
    print("Running scheduled task")

@app.on_event("startup")
async def start_scheduler():
    scheduler.add_job(scheduled_task, "interval", minutes=30)
    scheduler.start()
```

## Best Practices

1. **Keep tasks lightweight** - Background tasks should be quick
2. **Handle errors gracefully** - Always use try/except in tasks
3. **Log task execution** - Track what tasks run and their results
4. **Don't rely on return values** - Background tasks run after response
5. **Test thoroughly** - Background tasks can hide errors
6. **Consider task queues** - For production, consider Celery/RQ
7. **Monitor task performance** - Track execution time
8. **Avoid shared state** - Pass all needed data as parameters

## Key Points

- Background tasks run after the response is sent
- Use `BackgroundTasks` parameter in path operations
- Add tasks with `.add_task(function, *args, **kwargs)`
- Tasks run sequentially in the order added
- Works with both sync and async functions
- Tasks from dependencies execute before path operation tasks
- For heavy tasks, use Celery or similar task queues
- Always handle errors within background tasks
- Background tasks are not persisted if server restarts

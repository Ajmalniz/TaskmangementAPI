# Agent Integration Reference

Complete guide to integrating AI agents with FastAPI, transforming your REST API into a conversational interface that agents can interact with naturally.

## Table of Contents
- Why Agent Integration Matters
- The Integration Pattern
- Installing OpenAI Agents SDK
- Creating Tool Functions from CRUD Operations
- Wrapping Functions with @function_tool
- Building the Agent
- Non-Streaming Agent Endpoint
- Streaming Agent Endpoint with SSE
- Complete Working Example
- Hands-On Exercise
- Common Mistakes
- Best Practices

## Why Agent Integration Matters

**The Problem: APIs Are Not Conversational**

Traditional REST APIs require precise knowledge of endpoints, HTTP methods, and data formats:

```bash
# User must know exact endpoint and format
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn FastAPI", "description": "Complete tutorial"}'

# Then remember to GET the list
curl http://localhost:8000/tasks
```

**Users must know:**
- Exact endpoint paths (/tasks, /tasks/{id})
- HTTP methods (GET, POST, PUT, DELETE)
- JSON structure for request bodies
- Response formats and status codes

**The Solution: Conversational Agent Interface**

With agent integration, users interact naturally:

```
User: "Create a task called Learn FastAPI with description Complete tutorial"
Agent: "Created task 1: Learn FastAPI (status: pending)"

User: "Show me all my tasks"
Agent: "You have 1 task: Learn FastAPI (pending)"

User: "Mark it as completed"
Agent: "Updated task 1 to completed status"
```

**Why this matters for your API:**

1. **Natural language interface** - No need to remember endpoints or formats
2. **Intelligent orchestration** - Agent decides which tools to call and in what order
3. **Error recovery** - Agent can handle failures gracefully and retry
4. **Multi-step operations** - "Create three tasks and mark the first one as complete"
5. **Digital FTE service** - Your API becomes a "digital employee" that understands instructions

**The best part:** Your REST API still works normally! Agent integration is an additional interface, not a replacement.

## The Integration Pattern

The integration follows a clear pattern:

```
1. API Endpoints (REST)
   ↓
2. Tool Functions (Python functions that wrap endpoint logic)
   ↓
3. Decorated Tools (@function_tool makes them callable by agent)
   ↓
4. Agent (Orchestrates tools based on natural language)
   ↓
5. Streaming Endpoint (Exposes agent via SSE for real-time responses)
```

**Example: Task API**

Your Task API has these endpoints:

```python
POST   /tasks          # Create task
GET    /tasks          # List tasks
GET    /tasks/{id}     # Get single task
PUT    /tasks/{id}     # Update task
DELETE /tasks/{id}     # Delete task
```

**Step 1: Create tool functions** that wrap the CRUD logic:

```python
def create_task(title: str, description: str | None = None) -> dict:
    """Create a new task."""
    # CRUD logic here
    return {"id": 1, "title": title, "status": "pending"}
```

**Step 2: Decorate with @function_tool** so agent can call them:

```python
from agents import function_tool

@function_tool
def tool_create_task(title: str, description: str | None = None) -> str:
    """Create a new task with the given title and optional description."""
    result = create_task(title, description)
    return f"Created task {result['id']}: {result['title']}"
```

**Step 3: Build the agent** with all tools:

```python
from agents import Agent

task_agent = Agent(
    name="Task Manager",
    instructions="Help manage tasks. Create, list, update, and delete as requested.",
    tools=[tool_create_task, tool_list_tasks, tool_get_task,
           tool_update_status, tool_delete_task]
)
```

**Step 4: Expose via endpoint** with streaming:

```python
@app.post("/agent/chat/stream")
async def chat_with_agent_stream(request: ChatRequest):
    async def agent_stream():
        result = Runner.run_streamed(task_agent, request.message)
        async for event in result.stream_events():
            # Stream tokens as they arrive
            yield {"event": "token", "data": json.dumps({"text": text})}

    return EventSourceResponse(agent_stream())
```

Now users can chat with your API naturally!

## Installing OpenAI Agents SDK

The OpenAI Agents SDK provides the agent framework and function calling capabilities.

**Installation:**

```bash
uv add openai-agents
```

**What you get:**

- `Agent` - Create AI agents with instructions and tools
- `@function_tool` - Decorator to make functions callable by agents
- `Runner` - Execute agents with `run()` and `run_streamed()`
- Built-in function calling and tool orchestration

**Import in your code:**

```python
from agents import Agent, function_tool, Runner
```

**Environment variable:**

You'll need an OpenAI API key:

```bash
# .env
OPENAI_API_KEY=sk-your-api-key-here
```

**Load in code:**

```python
import os
from dotenv import load_dotenv

load_dotenv()
# API key automatically used by openai-agents
```

**Alternative: Use Anthropic SDK**

You can also use Anthropic's Claude with tool use:

```bash
uv add anthropic
```

```python
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Create a task"}],
    tools=[...],  # Tool definitions
)
```

This guide focuses on openai-agents for simplicity, but the pattern works with any agent framework.

## Creating Tool Functions from CRUD Operations

Tool functions are regular Python functions that wrap your CRUD logic. They should be independent of the FastAPI request/response cycle.

**Key principles:**

1. **Clear docstrings** - Agent reads these to understand what the tool does
2. **Type hints** - Required for agent to understand parameters
3. **JSON-serializable returns** - Dictionaries and primitives only
4. **Manage their own database sessions** - Don't rely on FastAPI's dependency injection
5. **Return human-readable results** - Agent will use these in responses

**Example: Create Task Tool**

```python
from sqlmodel import Session, select
from database import engine
from models import Task

def create_task(title: str, description: str | None = None) -> dict:
    """
    Create a new task with the given title and optional description.

    Args:
        title: The task title (required)
        description: Optional task description

    Returns:
        Dictionary with task details: id, title, description, status
    """
    with Session(engine) as session:
        task = Task(title=title, description=description, status="pending")
        session.add(task)
        session.commit()
        session.refresh(task)

        # Return dict, not SQLModel instance!
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status
        }
```

**Example: List Tasks Tool**

```python
def list_tasks(status: str | None = None) -> dict:
    """
    List all tasks, optionally filtered by status.

    Args:
        status: Optional status filter (pending, in_progress, completed)

    Returns:
        Dictionary with list of tasks
    """
    with Session(engine) as session:
        statement = select(Task)

        if status:
            statement = statement.where(Task.status == status)

        tasks = session.exec(statement).all()

        # Convert to dict list
        return {
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status
                }
                for task in tasks
            ],
            "count": len(tasks)
        }
```

**Example: Update Task Tool**

```python
def update_task_status(task_id: int, status: str) -> dict:
    """
    Update a task's status.

    Args:
        task_id: The ID of the task to update
        status: New status (pending, in_progress, completed)

    Returns:
        Dictionary with updated task details or error message
    """
    with Session(engine) as session:
        task = session.get(Task, task_id)

        if not task:
            return {
                "success": False,
                "error": f"Task {task_id} not found"
            }

        task.status = status
        session.add(task)
        session.commit()
        session.refresh(task)

        return {
            "success": True,
            "id": task.id,
            "title": task.title,
            "status": task.status
        }
```

**Example: Delete Task Tool**

```python
def delete_task(task_id: int) -> dict:
    """
    Delete a task by ID.

    Args:
        task_id: The ID of the task to delete

    Returns:
        Dictionary with success status and message
    """
    with Session(engine) as session:
        task = session.get(Task, task_id)

        if not task:
            return {
                "success": False,
                "error": f"Task {task_id} not found"
            }

        title = task.title
        session.delete(task)
        session.commit()

        return {
            "success": True,
            "message": f"Deleted task: {title}"
        }
```

**Key pattern - Separate file (tools.py):**

```python
# tools.py - CRUD functions without FastAPI dependencies
def create_task(...): ...
def list_tasks(...): ...
def get_task(...): ...
def update_task_status(...): ...
def delete_task(...): ...
```

These functions can be called from:
- FastAPI endpoints (via dependency injection)
- Agent tools (directly)
- Background tasks
- CLI commands
- Tests

## Wrapping Functions with @function_tool

The `@function_tool` decorator transforms regular Python functions into tools that agents can call.

**Basic pattern:**

```python
from agents import function_tool

@function_tool
def tool_create_task(title: str, description: str | None = None) -> str:
    """Create a new task with the given title and optional description."""
    result = create_task(title, description)
    return f"Created task {result['id']}: {result['title']}"
```

**Key points:**

1. **Docstring is the tool description** - Agent reads this to understand when to use the tool
2. **Type hints are required** - Agent needs to know parameter types
3. **Return string for agent** - Format the result as human-readable text
4. **Name should be descriptive** - `tool_create_task` not just `create`

**Complete example with all tools:**

```python
# agent.py
from agents import function_tool
from tools import (
    create_task,
    list_tasks,
    get_task,
    update_task_status,
    delete_task
)

@function_tool
def tool_create_task(title: str, description: str | None = None) -> str:
    """Create a new task with the given title and optional description."""
    result = create_task(title, description)

    if not result.get("success", True):
        return f"Error: {result['error']}"

    return f"Created task {result['id']}: {result['title']} (status: {result['status']})"

@function_tool
def tool_list_tasks(status: str | None = None) -> str:
    """List all tasks, optionally filtered by status (pending, in_progress, completed)."""
    result = list_tasks(status)

    if result["count"] == 0:
        return "No tasks found."

    tasks_str = "\n".join([
        f"- Task {task['id']}: {task['title']} ({task['status']})"
        for task in result["tasks"]
    ])

    return f"Found {result['count']} tasks:\n{tasks_str}"

@function_tool
def tool_get_task(task_id: int) -> str:
    """Get details of a specific task by ID."""
    result = get_task(task_id)

    if not result.get("success", True):
        return f"Error: {result['error']}"

    task = result["task"]
    return f"Task {task['id']}: {task['title']}\nStatus: {task['status']}\nDescription: {task['description'] or 'None'}"

@function_tool
def tool_update_status(task_id: int, status: str) -> str:
    """Update a task's status. Status must be: pending, in_progress, or completed."""
    result = update_task_status(task_id, status)

    if not result.get("success"):
        return f"Error: {result['error']}"

    return f"Updated task {task_id} to status: {status}"

@function_tool
def tool_delete_task(task_id: int) -> str:
    """Delete a task by ID."""
    result = delete_task(task_id)

    if not result.get("success"):
        return f"Error: {result['error']}"

    return result["message"]
```

**Why separate function from tool?**

```python
# ✅ CORRECT - Separation of concerns
def create_task(...) -> dict:
    """CRUD logic - returns dict"""
    ...

@function_tool
def tool_create_task(...) -> str:
    """Agent tool - formats response as string"""
    result = create_task(...)
    return f"Created task {result['id']}"

# ❌ WRONG - Mixing concerns
@function_tool
def tool_create_task(...) -> str:
    """Does CRUD and formats in one function"""
    # Hard to test and reuse!
```

**Benefits of separation:**

- CRUD functions can be reused in endpoints, tests, CLI
- Agent tools focus on formatting responses
- Easier to test each layer independently
- Clear separation of concerns

## Building the Agent

The `Agent` class orchestrates tools based on natural language instructions.

**Basic agent structure:**

```python
from agents import Agent

task_agent = Agent(
    name="Task Manager",
    instructions="You help users manage their tasks. You can create, list, update, and delete tasks based on user requests.",
    tools=[tool_create_task, tool_list_tasks, tool_get_task, tool_update_status, tool_delete_task]
)
```

**Key parameters:**

- **name** - Agent's name (appears in logs and responses)
- **instructions** - System prompt that guides agent behavior
- **tools** - List of @function_tool decorated functions

**Writing good instructions:**

```python
# ✅ CORRECT - Clear, specific instructions
task_agent = Agent(
    name="Task Manager",
    instructions="""You help users manage their tasks.

Available operations:
- Create tasks with title and optional description
- List all tasks or filter by status (pending, in_progress, completed)
- Get details of a specific task
- Update task status
- Delete tasks

When users ask about tasks:
1. Use appropriate tools to fulfill the request
2. Provide clear, friendly responses
3. If a task ID is needed but not provided, list tasks first
4. Confirm destructive operations (like delete) before executing

Always be helpful and confirm what you've done.""",
    tools=[...]
)

# ❌ WRONG - Too vague
task_agent = Agent(
    name="Task Manager",
    instructions="Help with tasks",
    tools=[...]
)
```

**Agent with model configuration:**

```python
task_agent = Agent(
    name="Task Manager",
    instructions="...",
    tools=[...],
    model="gpt-4o",  # Specify model
    temperature=0.7,  # Control randomness
)
```

**Multiple agents pattern:**

```python
# Different agents for different domains
task_agent = Agent(
    name="Task Manager",
    instructions="Manage tasks...",
    tools=[task_tools]
)

user_agent = Agent(
    name="User Manager",
    instructions="Manage users...",
    tools=[user_tools]
)

# Route to appropriate agent based on intent
if "task" in message.lower():
    result = Runner.run(task_agent, message)
else:
    result = Runner.run(user_agent, message)
```

**Agent with handoffs (advanced):**

```python
# Main agent can delegate to specialized agents
main_agent = Agent(
    name="Main Assistant",
    instructions="Route requests to appropriate specialist agents",
    tools=[handoff_to_task_agent, handoff_to_user_agent]
)
```

## Non-Streaming Agent Endpoint

The simplest agent endpoint waits for the complete response before returning.

**Basic pattern:**

```python
from pydantic import BaseModel
from agents import Runner

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/agent/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """Chat with the task management agent."""
    result = await Runner.run(task_agent, request.message)
    return {"response": result.final_output}
```

**How it works:**

1. User sends natural language message
2. `Runner.run()` orchestrates agent with tools
3. Agent decides which tools to call
4. Returns complete response when done

**Testing with curl:**

```bash
# Create a task
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a task called Learn FastAPI"}'

# Response:
# {"response": "Created task 1: Learn FastAPI (status: pending)"}

# List tasks
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all my tasks"}'

# Response:
# {"response": "Found 1 tasks:\n- Task 1: Learn FastAPI (pending)"}

# Update status
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Mark task 1 as completed"}'

# Response:
# {"response": "Updated task 1 to status: completed"}
```

**With error handling:**

```python
@app.post("/agent/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """Chat with the task management agent."""
    try:
        result = await Runner.run(task_agent, request.message)
        return {"response": result.final_output}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )
```

**Limitations of non-streaming:**

- User waits for complete response (no real-time feedback)
- Can feel slow for multi-step operations
- No visibility into what agent is doing
- Not ideal for long-running tasks

**When to use non-streaming:**

- Quick operations (< 2 seconds)
- Simple single-tool calls
- Testing and development
- When streaming complexity isn't worth it

**For production agent APIs, use streaming instead!**

## Streaming Agent Endpoint with SSE

Streaming provides real-time feedback as the agent thinks and calls tools.

**Complete streaming implementation:**

```python
from sse_starlette.sse import EventSourceResponse
from agents import Runner
import json

@app.post("/agent/chat/stream")
async def chat_with_agent_stream(request: ChatRequest):
    """Chat with the agent using streaming for real-time responses."""

    async def agent_stream_generator(message: str):
        try:
            # Run agent with streaming
            result = Runner.run_streamed(task_agent, message)

            # Stream events as they occur
            async for event in result.stream_events():
                # Token events (agent thinking/responding)
                if event.type == "raw_response_event":
                    if hasattr(event.data, 'delta') and hasattr(event.data.delta, 'text'):
                        text = event.data.delta.text
                        if text:
                            yield {
                                "event": "token",
                                "data": json.dumps({"text": text})
                            }

                # Tool call events
                elif event.type == "tool_call_event":
                    yield {
                        "event": "tool_call",
                        "data": json.dumps({
                            "tool": event.tool_name,
                            "args": event.arguments
                        })
                    }

                # Tool result events
                elif event.type == "tool_result_event":
                    yield {
                        "event": "tool_result",
                        "data": json.dumps({
                            "tool": event.tool_name,
                            "result": event.result
                        })
                    }

            # Final completion event
            yield {
                "event": "complete",
                "data": json.dumps({
                    "response": result.final_output
                })
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(agent_stream_generator(request.message))
```

**Event types you'll see:**

1. **token** - Agent's response text, word by word
2. **tool_call** - When agent decides to call a tool
3. **tool_result** - Result from tool execution
4. **complete** - Final response
5. **error** - If something goes wrong

**Testing with browser:**

```html
<!DOCTYPE html>
<html>
<head><title>Agent Chat</title></head>
<body>
    <div id="chat"></div>
    <input id="message" placeholder="Ask the agent...">
    <button onclick="sendMessage()">Send</button>

    <script>
        async function sendMessage() {
            const message = document.getElementById('message').value;
            const chat = document.getElementById('chat');

            // Show user message
            chat.innerHTML += `<p><strong>You:</strong> ${message}</p>`;

            // Connect to streaming endpoint
            const response = await fetch('/agent/chat/stream', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message})
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let agentResponse = '<p><strong>Agent:</strong> ';

            while (true) {
                const {done, value} = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const events = chunk.split('\n\n');

                for (const event of events) {
                    if (event.startsWith('data:')) {
                        const data = JSON.parse(event.slice(5));

                        if (data.text) {
                            agentResponse += data.text;
                            chat.innerHTML = chat.innerHTML.slice(0, -4) +
                                           data.text + '</p>';
                        }
                    }
                }
            }

            document.getElementById('message').value = '';
        }
    </script>
</body>
</html>
```

**Simpler streaming (text only):**

```python
@app.post("/agent/chat/stream")
async def chat_with_agent_stream(request: ChatRequest):
    """Simplified streaming - only tokens."""

    async def agent_stream():
        result = Runner.run_streamed(task_agent, request.message)

        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if hasattr(event.data, 'delta') and hasattr(event.data.delta, 'text'):
                    text = event.data.delta.text
                    if text:
                        yield {
                            "event": "message",
                            "data": json.dumps({"text": text})
                        }

        yield {
            "event": "complete",
            "data": json.dumps({"done": True})
        }

    return EventSourceResponse(agent_stream())
```

**Why streaming is better:**

- User sees agent thinking in real-time
- Shows tool calls as they happen
- Better perceived performance
- Can display progress indicators
- Essential for conversational UX

## Complete Working Example

A production-ready agent integration with all best practices:

**Project structure:**

```
task-agent-api/
├── .env                    # API keys
├── pyproject.toml          # Dependencies
├── config.py               # Settings
├── database.py             # Database setup
├── models.py               # SQLModel models
├── tools.py                # CRUD functions
├── agent.py                # Agent and decorated tools
└── main.py                 # FastAPI app
```

**config.py:**

```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    openai_api_key: str

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**models.py:**

```python
from sqlmodel import SQLModel, Field
from typing import Optional

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    status: str = Field(default="pending")  # pending, in_progress, completed
```

**database.py:**

```python
from sqlmodel import create_engine
from config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, echo=True)
```

**tools.py:**

```python
from sqlmodel import Session, select
from database import engine
from models import Task

def create_task(title: str, description: str | None = None) -> dict:
    """Create a new task."""
    with Session(engine) as session:
        task = Task(title=title, description=description)
        session.add(task)
        session.commit()
        session.refresh(task)
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status
        }

def list_tasks(status: str | None = None) -> dict:
    """List all tasks."""
    with Session(engine) as session:
        statement = select(Task)
        if status:
            statement = statement.where(Task.status == status)
        tasks = session.exec(statement).all()
        return {
            "tasks": [
                {"id": t.id, "title": t.title, "description": t.description, "status": t.status}
                for t in tasks
            ],
            "count": len(tasks)
        }

def get_task(task_id: int) -> dict:
    """Get a single task."""
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            return {"success": False, "error": f"Task {task_id} not found"}
        return {
            "success": True,
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status
            }
        }

def update_task_status(task_id: int, status: str) -> dict:
    """Update task status."""
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            return {"success": False, "error": f"Task {task_id} not found"}
        task.status = status
        session.add(task)
        session.commit()
        return {"success": True, "id": task.id, "status": task.status}

def delete_task(task_id: int) -> dict:
    """Delete a task."""
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            return {"success": False, "error": f"Task {task_id} not found"}
        title = task.title
        session.delete(task)
        session.commit()
        return {"success": True, "message": f"Deleted task: {title}"}
```

**agent.py:**

```python
from agents import Agent, function_tool
from tools import create_task, list_tasks, get_task, update_task_status, delete_task

@function_tool
def tool_create_task(title: str, description: str | None = None) -> str:
    """Create a new task with the given title and optional description."""
    result = create_task(title, description)
    return f"Created task {result['id']}: {result['title']} (status: {result['status']})"

@function_tool
def tool_list_tasks(status: str | None = None) -> str:
    """List all tasks, optionally filtered by status (pending, in_progress, completed)."""
    result = list_tasks(status)
    if result["count"] == 0:
        return "No tasks found."
    tasks_str = "\n".join([
        f"- Task {t['id']}: {t['title']} ({t['status']})"
        for t in result["tasks"]
    ])
    return f"Found {result['count']} tasks:\n{tasks_str}"

@function_tool
def tool_get_task(task_id: int) -> str:
    """Get details of a specific task by ID."""
    result = get_task(task_id)
    if not result.get("success", True):
        return f"Error: {result['error']}"
    t = result["task"]
    return f"Task {t['id']}: {t['title']}\nStatus: {t['status']}\nDescription: {t['description'] or 'None'}"

@function_tool
def tool_update_status(task_id: int, status: str) -> str:
    """Update a task's status. Status must be: pending, in_progress, or completed."""
    result = update_task_status(task_id, status)
    if not result.get("success"):
        return f"Error: {result['error']}"
    return f"Updated task {task_id} to status: {status}"

@function_tool
def tool_delete_task(task_id: int) -> str:
    """Delete a task by ID."""
    result = delete_task(task_id)
    if not result.get("success"):
        return f"Error: {result['error']}"
    return result["message"]

# Create the agent
task_agent = Agent(
    name="Task Manager",
    instructions="""You are a helpful task management assistant.

You can:
- Create tasks with title and optional description
- List all tasks or filter by status (pending, in_progress, completed)
- Get details of specific tasks
- Update task status
- Delete tasks

When users ask about tasks:
1. Use the appropriate tool to fulfill their request
2. Provide clear, friendly responses
3. If a task ID is needed but not provided, list tasks first
4. Confirm what you've done

Always be helpful and conversational.""",
    tools=[
        tool_create_task,
        tool_list_tasks,
        tool_get_task,
        tool_update_status,
        tool_delete_task
    ]
)
```

**main.py:**

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from agents import Runner
import json

from database import engine
from agent import task_agent
import models  # Import for create_all

app = FastAPI(title="Task Agent API")

# CORS for browser clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def create_db_and_tables():
    """Create database tables on startup."""
    SQLModel.metadata.create_all(engine)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    return {
        "message": "Task Agent API",
        "endpoints": {
            "chat": "POST /agent/chat",
            "chat_stream": "POST /agent/chat/stream"
        }
    }

@app.post("/agent/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """Non-streaming agent chat."""
    try:
        result = await Runner.run(task_agent, request.message)
        return {"response": result.final_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/chat/stream")
async def chat_with_agent_stream(request: ChatRequest):
    """Streaming agent chat with real-time responses."""

    async def agent_stream():
        try:
            result = Runner.run_streamed(task_agent, request.message)

            async for event in result.stream_events():
                if event.type == "raw_response_event":
                    if hasattr(event.data, 'delta') and hasattr(event.data.delta, 'text'):
                        text = event.data.delta.text
                        if text:
                            yield {
                                "event": "token",
                                "data": json.dumps({"text": text})
                            }

            yield {
                "event": "complete",
                "data": json.dumps({"response": result.final_output})
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(agent_stream())
```

**.env:**

```bash
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
OPENAI_API_KEY=sk-your-api-key-here
```

**Install dependencies:**

```bash
uv add "fastapi[standard]" sqlmodel psycopg2-binary pydantic-settings openai-agents sse-starlette
```

**Run the app:**

```bash
uv run uvicorn main:app --reload
```

**Test it:**

```bash
# Non-streaming
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create three tasks: Learn FastAPI, Build an API, Deploy to production"}'

# Streaming
curl -N -X POST http://localhost:8000/agent/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all pending tasks"}'
```

## Hands-On Exercise

Build a complete agent-integrated Task API from scratch.

**Step 1: Initialize project**

```bash
uv init task-agent-api
cd task-agent-api
uv add "fastapi[standard]" sqlmodel psycopg2-binary pydantic-settings openai-agents sse-starlette python-dotenv
```

**Step 2: Create .env**

```bash
# .env
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
OPENAI_API_KEY=sk-your-api-key-here
```

**Step 3: Create models.py**

```python
from sqlmodel import SQLModel, Field
from typing import Optional

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    status: str = Field(default="pending")
```

**Step 4: Create database.py**

```python
from sqlmodel import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"), echo=True)
```

**Step 5: Create tools.py**

Implement these functions:
- `create_task(title, description) -> dict`
- `list_tasks(status) -> dict`
- `update_task_status(task_id, status) -> dict`

**Step 6: Create agent.py**

Decorate your tools and create the agent:

```python
from agents import Agent, function_tool
from tools import create_task, list_tasks, update_task_status

@function_tool
def tool_create_task(title: str, description: str | None = None) -> str:
    # TODO: Call create_task and format response
    pass

# TODO: Add more decorated tools

task_agent = Agent(
    name="Task Manager",
    instructions="Help manage tasks...",
    tools=[tool_create_task]  # Add all tools
)
```

**Step 7: Create main.py**

Add both streaming and non-streaming endpoints.

**Step 8: Test your agent**

```bash
# Run server
uv run uvicorn main:app --reload

# Test in another terminal
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a task called Test Agent Integration"}'
```

**Step 9: Test streaming**

Create a simple HTML test page or use curl with -N flag.

**Step 10: Try natural language queries**

```bash
# Multi-step operation
"Create three tasks: one for learning, one for building, and one for testing"

# Filtering
"Show me only the pending tasks"

# Updates
"Mark the first task as completed"

# Conditional
"If there are more than 5 tasks, delete the oldest one"
```

## Common Mistakes

**Mistake 1: Missing docstrings on tools**

```python
# ❌ WRONG - Agent doesn't know what this does!
@function_tool
def tool_create(title: str) -> str:
    result = create_task(title)
    return f"Created {result['id']}"

# ✅ CORRECT - Clear description
@function_tool
def tool_create_task(title: str, description: str | None = None) -> str:
    """Create a new task with the given title and optional description."""
    result = create_task(title, description)
    return f"Created task {result['id']}: {result['title']}"
```

**Mistake 2: Returning complex objects**

```python
# ❌ WRONG - Returns SQLModel instance (not JSON-serializable)
def create_task(title: str) -> Task:
    task = Task(title=title)
    session.add(task)
    session.commit()
    return task  # Can't be serialized!

# ✅ CORRECT - Returns dict
def create_task(title: str) -> dict:
    task = Task(title=title)
    session.add(task)
    session.commit()
    session.refresh(task)
    return {"id": task.id, "title": task.title}  # JSON-serializable
```

**Mistake 3: Not handling None/null cases**

```python
# ❌ WRONG - Crashes if task not found!
def get_task(task_id: int) -> dict:
    task = session.get(Task, task_id)
    return {"id": task.id, "title": task.title}  # task might be None!

# ✅ CORRECT - Handles None
def get_task(task_id: int) -> dict:
    task = session.get(Task, task_id)
    if not task:
        return {"success": False, "error": f"Task {task_id} not found"}
    return {"success": True, "task": {"id": task.id, "title": task.title}}
```

**Mistake 4: Vague tool descriptions**

```python
# ❌ WRONG - Not clear what this does
@function_tool
def tool_update(id: int, status: str) -> str:
    """Update something."""
    ...

# ✅ CORRECT - Specific and clear
@function_tool
def tool_update_task_status(task_id: int, status: str) -> str:
    """Update a task's status. Status must be one of: pending, in_progress, or completed."""
    ...
```

**Mistake 5: Missing type hints**

```python
# ❌ WRONG - Agent doesn't know parameter types!
@function_tool
def tool_create_task(title, description=None):
    """Create a task."""
    ...

# ✅ CORRECT - Type hints required
@function_tool
def tool_create_task(title: str, description: str | None = None) -> str:
    """Create a task."""
    ...
```

**Mistake 6: Not formatting responses for humans**

```python
# ❌ WRONG - Returns dict as string (ugly)
@function_tool
def tool_list_tasks() -> str:
    result = list_tasks()
    return str(result)  # "{'tasks': [{'id': 1, 'title': '...'}]}"

# ✅ CORRECT - Formatted for humans
@function_tool
def tool_list_tasks() -> str:
    result = list_tasks()
    if result["count"] == 0:
        return "No tasks found."
    tasks_str = "\n".join([f"- {t['title']}" for t in result["tasks"]])
    return f"Found {result['count']} tasks:\n{tasks_str}"
```

**Mistake 7: Forgetting to load environment variables**

```python
# ❌ WRONG - API key not loaded!
from agents import Agent

task_agent = Agent(...)  # Fails! No OPENAI_API_KEY

# ✅ CORRECT - Load .env first
from dotenv import load_dotenv
load_dotenv()  # Must call before using openai-agents

from agents import Agent
task_agent = Agent(...)
```

**Mistake 8: Not handling streaming events properly**

```python
# ❌ WRONG - Missing event type checks
async def agent_stream():
    result = Runner.run_streamed(agent, message)
    async for event in result.stream_events():
        # Crashes if event doesn't have .data.delta.text!
        yield {"data": json.dumps({"text": event.data.delta.text})}

# ✅ CORRECT - Check event types and attributes
async def agent_stream():
    result = Runner.run_streamed(agent, message)
    async for event in result.stream_events():
        if event.type == "raw_response_event":
            if hasattr(event.data, 'delta') and hasattr(event.data.delta, 'text'):
                text = event.data.delta.text
                if text:
                    yield {"event": "token", "data": json.dumps({"text": text})}
```

## Best Practices

**1. Clear tool descriptions**

Write docstrings that explain:
- What the tool does
- What parameters it needs
- What format they should be in
- What it returns

```python
@function_tool
def tool_create_task(title: str, description: str | None = None) -> str:
    """
    Create a new task with the given title and optional description.

    Args:
        title: The task title (required, 1-200 characters)
        description: Optional task description

    Returns:
        Success message with task ID and title
    """
    ...
```

**2. Always return JSON-serializable data**

```python
# ✅ GOOD
def create_task(...) -> dict:
    return {"id": 1, "title": "Task", "status": "pending"}

# ❌ BAD
def create_task(...) -> Task:
    return Task(...)  # SQLModel instance not serializable
```

**3. Handle errors gracefully**

```python
def get_task(task_id: int) -> dict:
    task = session.get(Task, task_id)
    if not task:
        return {
            "success": False,
            "error": f"Task {task_id} not found"
        }
    return {
        "success": True,
        "task": {...}
    }
```

**4. Format responses for humans**

```python
@function_tool
def tool_list_tasks() -> str:
    result = list_tasks()
    # Format nicely for agent to show user
    tasks_str = "\n".join([
        f"- Task {t['id']}: {t['title']} ({t['status']})"
        for t in result["tasks"]
    ])
    return f"Found {result['count']} tasks:\n{tasks_str}"
```

**5. Separate concerns: CRUD → Tools → Agent → Endpoint**

```
tools.py          → CRUD functions (return dicts)
agent.py          → @function_tool wrappers (return strings)
main.py           → FastAPI endpoints (return responses)
```

**6. Test tools independently**

```python
# Test CRUD function
def test_create_task():
    result = create_task("Test", "Description")
    assert result["title"] == "Test"

# Test tool wrapper
def test_tool_create_task():
    response = tool_create_task("Test")
    assert "Created task" in response
```

**7. Use streaming for better UX**

Streaming shows:
- Agent thinking in real-time
- Tool calls as they happen
- Progress for long operations
- Better perceived performance

**8. Validate tool parameters**

```python
@function_tool
def tool_update_status(task_id: int, status: str) -> str:
    """Update task status. Status must be: pending, in_progress, or completed."""
    valid_statuses = ["pending", "in_progress", "completed"]
    if status not in valid_statuses:
        return f"Error: Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"

    result = update_task_status(task_id, status)
    ...
```

**9. Log agent interactions**

```python
import logging

logger = logging.getLogger(__name__)

@app.post("/agent/chat")
async def chat_with_agent(request: ChatRequest):
    logger.info(f"Agent query: {request.message}")
    result = await Runner.run(task_agent, request.message)
    logger.info(f"Agent response: {result.final_output}")
    return {"response": result.final_output}
```

**10. Provide clear agent instructions**

```python
task_agent = Agent(
    name="Task Manager",
    instructions="""You are a helpful task management assistant.

IMPORTANT GUIDELINES:
- Always confirm what you've done
- If a task ID is needed but not provided, list tasks first
- Be conversational and friendly
- Validate status values (pending, in_progress, completed)
- Ask for confirmation before deleting tasks

Example interactions:
User: "Create a task"
You: "Sure! What should the task title be?"

User: "Mark task 5 as done"
You: "I'll update task 5 to completed status..." [calls tool] "Done! Task 5 is now completed."
""",
    tools=[...]
)
```

## Key Points

- Agent integration transforms REST APIs into conversational interfaces
- Use `openai-agents` SDK: `uv add openai-agents`
- Pattern: CRUD functions → @function_tool wrappers → Agent → Streaming endpoint
- Tool functions must have docstrings, type hints, and return JSON-serializable data
- `@function_tool` decorator makes functions callable by agents
- `Agent` orchestrates tools based on instructions and user messages
- Use `Runner.run()` for non-streaming, `Runner.run_streamed()` for streaming
- Streaming with SSE provides real-time feedback for better UX
- Always handle errors gracefully and return human-readable messages
- Separate concerns: tools.py (CRUD) → agent.py (decorated tools) → main.py (endpoints)
- Agent integration adds conversational interface without replacing REST API
- Digital FTE pattern: Your API becomes an AI employee that understands natural language

# Streaming with SSE (Server-Sent Events) Reference

Complete guide to implementing real-time streaming in FastAPI using Server-Sent Events (SSE). Essential for agent APIs where users need to see responses forming in real-time.

## Table of Contents
- Why Streaming Changes Everything
- How SSE Works (Under the Hood)
- Installing sse-starlette
- Your First Streaming Endpoint
- Why Async Generators Matter for Agents
- Testing in Browser
- Streaming with Context
- Error Handling in Streams
- Complete Streaming Example
- Hands-On Exercise
- Challenge: Build a Progress Tracker
- Common Mistakes

## Why Streaming Changes Everything

**The Problem: Traditional Request-Response Feels Slow**

```python
# ❌ Traditional: User waits 10 seconds for complete response
@app.post("/process")
async def process_task(task: str):
    result = await long_running_process(task)  # Takes 10 seconds
    return {"result": result}  # User sees nothing until done!
```

**Traditional request-response:**
- Client sends request
- Server processes (user waits with no feedback)
- Server sends complete response
- Client receives entire response at once

**For long operations (10+ seconds), this feels broken:**
- User doesn't know if anything is happening
- No feedback during processing
- Can't tell if it failed or is still working
- Entire result arrives at once (or nothing)

**The Solution: Streaming with SSE**

```python
# ✅ Streaming: User sees updates every second
@app.get("/process/stream")
async def stream_process():
    async def generate():
        for step in ["Analyzing", "Processing", "Finalizing"]:
            yield {"event": "progress", "data": json.dumps({"step": step})}
            await asyncio.sleep(1)
        yield {"event": "complete", "data": json.dumps({"result": "Done!"})}

    return EventSourceResponse(generate())
```

**Streaming updates:**
- Server sends data as it becomes available
- Client receives updates in real-time
- User sees progress immediately
- Better perceived performance
- Failed operations fail fast (don't wait 10 seconds to see error)

**Benefits for Agent APIs:**

1. **Real-time feedback** - Users see agent "thinking" and making progress
2. **Better perceived performance** - First byte matters more than last byte
3. **Transparency** - Show intermediate steps, reasoning, tool calls
4. **Failed operations fail fast** - Errors appear immediately, not after timeout
5. **Token-by-token LLM responses** - Natural reading experience (like ChatGPT)

**Example: LLM Agent Streaming**

Without streaming:
```
[User waits 15 seconds...]
Complete response appears: "I analyzed your request, called the weather API,
formatted the data, and here's your 5-day forecast..."
```

With streaming:
```
[Immediate feedback]
"I'll help with that weather forecast..."
[2 seconds]
"Calling weather API..."
[3 seconds]
"Retrieved data for New York..."
[1 second]
"Here's your 5-day forecast..."
```

The total time is the same, but streaming feels **much faster** because the first byte arrives immediately.

## How SSE Works (Under the Hood)

**SSE is Just HTTP with a Special Format**

Server-Sent Events (SSE) is a simple protocol for streaming data over HTTP:

```
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

event: message
data: {"text": "Hello"}

event: message
data: {"text": "World"}

event: complete
data: {"done": true}

```

**SSE Message Format:**

Each message has three parts:
1. `event:` - Event type (optional, defaults to "message")
2. `data:` - Event payload (must be a string)
3. Blank line - Marks end of message

**Example SSE stream:**

```
event: task_update
data: {"progress": 20, "step": "Analyzing"}

event: task_update
data: {"progress": 40, "step": "Processing"}

event: task_update
data: {"progress": 60, "step": "Formatting"}

event: complete
data: {"result": "Success"}

```

**Why SSE Over WebSockets?**

| Feature | SSE | WebSockets |
|---------|-----|------------|
| Direction | Server → Client | Bidirectional |
| Protocol | HTTP | Custom protocol |
| Reconnection | Automatic | Manual |
| Proxy Support | Works everywhere | Needs configuration |
| Complexity | Simple | Complex |
| Use Case | Server pushes updates | Real-time chat, games |

**SSE is perfect when:**
- Server pushes data to client (one-directional)
- Client doesn't need to send data back during stream
- You want automatic reconnection
- You need to work through corporate proxies

**WebSockets are better when:**
- Bidirectional communication is required
- Real-time gaming or chat
- Low latency is critical

**For agent APIs, SSE is usually the right choice:**
- Agent streams results to client
- Client doesn't interrupt the stream
- Simpler to implement and deploy
- Better proxy compatibility

**Browser Support:**

All modern browsers support SSE through the `EventSource` API:

```javascript
const eventSource = new EventSource('/stream');

eventSource.addEventListener('message', (event) => {
    console.log('Received:', event.data);
});

eventSource.addEventListener('complete', (event) => {
    console.log('Done:', event.data);
    eventSource.close();
});
```

## Installing sse-starlette

FastAPI doesn't include SSE support by default. Use the `sse-starlette` library:

```bash
uv add sse-starlette
```

**What you get:**

- `EventSourceResponse` - FastAPI response class for SSE
- Automatic formatting of SSE messages
- Proper content-type and headers
- Connection management

**Import in your code:**

```python
from sse_starlette.sse import EventSourceResponse
```

That's it! Now you can return `EventSourceResponse` from your endpoints.

## Your First Streaming Endpoint

**Step 1: Create an async generator**

An async generator is a function that:
- Uses `async def`
- Uses `yield` instead of `return`
- Can be paused and resumed

```python
async def my_generator():
    yield "First"
    await asyncio.sleep(1)
    yield "Second"
    await asyncio.sleep(1)
    yield "Third"
```

**Step 2: Wrap with EventSourceResponse**

```python
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

app = FastAPI()

@app.get("/stream")
async def stream_endpoint():
    async def event_generator():
        for i in range(5):
            # SSE message format
            yield {
                "event": "message",
                "data": json.dumps({"count": i})
            }
            await asyncio.sleep(1)

        # Send completion event
        yield {
            "event": "complete",
            "data": json.dumps({"done": True})
        }

    return EventSourceResponse(event_generator())
```

**What happens:**

1. Client connects to `/stream`
2. `event_generator()` starts yielding messages
3. Each `yield` sends one SSE message to client
4. `await asyncio.sleep(1)` pauses without blocking
5. After 5 messages, sends "complete" event
6. Connection closes

**Step 3: Test with curl**

```bash
curl -N http://localhost:8000/stream
```

Output:
```
event: message
data: {"count": 0}

event: message
data: {"count": 1}

event: message
data: {"count": 2}

event: message
data: {"count": 3}

event: message
data: {"count": 4}

event: complete
data: {"done": true}
```

**Key points:**

- **`yield` not `return`** - Generators yield multiple values
- **`json.dumps()`** - SSE data must be a string, not a dict
- **`await asyncio.sleep()`** - Non-blocking delay (NOT `time.sleep()`)
- **`EventSourceResponse`** - Handles SSE formatting and headers
- **`curl -N`** - Disables buffering to see stream in real-time

## Why Async Generators Matter for Agents

**Async generators are the foundation of streaming in FastAPI.**

**Regular function (returns once):**

```python
def get_result():
    result = do_work()
    return result  # Returns once, function ends
```

**Generator (yields multiple times):**

```python
def generate_results():
    for i in range(3):
        yield f"Result {i}"  # Yields, function pauses
    # Function ends after yielding all values
```

**Async generator (yields multiple times, non-blocking):**

```python
async def generate_results():
    for i in range(3):
        yield f"Result {i}"  # Yields, function pauses
        await asyncio.sleep(1)  # Non-blocking delay
```

**Why async generators are perfect for agents:**

1. **Stream LLM responses token-by-token**
   ```python
   async def stream_llm_response(prompt: str):
       async for token in llm.stream(prompt):
           yield {"event": "token", "data": json.dumps({"token": token})}
       yield {"event": "complete", "data": json.dumps({"done": True})}
   ```

2. **Show intermediate steps**
   ```python
   async def stream_agent_thinking():
       yield {"event": "thinking", "data": json.dumps({"step": "Planning"})}
       plan = await create_plan()

       yield {"event": "thinking", "data": json.dumps({"step": "Executing"})}
       result = await execute_plan(plan)

       yield {"event": "result", "data": json.dumps({"result": result})}
   ```

3. **Report tool calls in real-time**
   ```python
   async def stream_tool_usage():
       for tool in tools:
           yield {"event": "tool", "data": json.dumps({"calling": tool.name})}
           result = await tool.execute()
           yield {"event": "tool_result", "data": json.dumps({"result": result})}
   ```

**Connection to Real Agent Streaming:**

The pattern you're learning here is the same pattern used for real LLM streaming:

```python
# This lesson: Simulating with sleep
async def fake_llm_stream():
    for token in ["Hello", " ", "world", "!"]:
        yield {"event": "token", "data": json.dumps({"token": token})}
        await asyncio.sleep(0.1)

# Later: Real LLM streaming (Anthropic SDK)
async def real_llm_stream(prompt: str):
    async with client.messages.stream(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        async for text in stream.text_stream:
            yield {"event": "token", "data": json.dumps({"token": text})}
```

Same pattern, just different data sources!

## Testing in Browser

The browser has built-in support for SSE through the `EventSource` API.

**Create a test HTML file (test-sse.html):**

```html
<!DOCTYPE html>
<html>
<head>
    <title>SSE Test</title>
</head>
<body>
    <h1>Server-Sent Events Test</h1>
    <div id="messages"></div>
    <button id="start">Start Stream</button>
    <button id="stop">Stop Stream</button>

    <script>
        let eventSource = null;
        const messagesDiv = document.getElementById('messages');

        document.getElementById('start').addEventListener('click', () => {
            if (eventSource) {
                eventSource.close();
            }

            messagesDiv.innerHTML = '<p>Connecting...</p>';

            // Connect to SSE endpoint
            eventSource = new EventSource('http://localhost:8000/stream');

            // Listen for 'message' events (default)
            eventSource.addEventListener('message', (event) => {
                const data = JSON.parse(event.data);
                messagesDiv.innerHTML += `<p>Message: ${JSON.stringify(data)}</p>`;
            });

            // Listen for 'complete' events
            eventSource.addEventListener('complete', (event) => {
                const data = JSON.parse(event.data);
                messagesDiv.innerHTML += `<p><strong>Complete: ${JSON.stringify(data)}</strong></p>`;
                eventSource.close();
            });

            // Handle errors
            eventSource.addEventListener('error', (event) => {
                messagesDiv.innerHTML += `<p style="color: red;">Error: Connection failed</p>`;
                eventSource.close();
            });

            // Connection opened
            eventSource.addEventListener('open', (event) => {
                messagesDiv.innerHTML += `<p style="color: green;">Connected!</p>`;
            });
        });

        document.getElementById('stop').addEventListener('click', () => {
            if (eventSource) {
                eventSource.close();
                messagesDiv.innerHTML += `<p>Connection closed</p>`;
            }
        });
    </script>
</body>
</html>
```

**Serve the HTML file:**

```bash
# Option 1: Python's built-in server
python -m http.server 8080

# Option 2: Just open the file (but CORS might block it)
# In that case, add CORS middleware to your FastAPI app
```

**Add CORS to your FastAPI app (if needed):**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Test with fetch API (modern approach):**

```javascript
// Modern fetch-based approach (more control)
async function testSSE() {
    const response = await fetch('http://localhost:8000/stream');
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        console.log('Received chunk:', chunk);
    }
}

testSSE();
```

**EventSource vs Fetch:**

| EventSource | Fetch |
|-------------|-------|
| Simple, built-in parsing | Manual parsing |
| Automatic reconnection | Manual reconnection |
| Event-based API | Stream-based API |
| Read-only (GET requests) | Full control |

**Swagger UI Limitations:**

⚠️ **Important:** Swagger UI doesn't support SSE streaming!

```python
@app.get("/stream")
async def stream():
    return EventSourceResponse(generate())
```

If you try this in Swagger UI:
- It will wait for the entire stream to finish
- Then show all data at once
- SSE formatting is lost

**Always test SSE endpoints with:**
- Browser `EventSource` API
- `curl -N`
- Custom HTML test page
- Fetch API

Don't rely on Swagger UI for streaming endpoints!

## Streaming with Context

Real applications need to stream task-specific updates, not just counters.

**Example 1: Task Processing Stream**

```python
from typing import Literal

@app.post("/tasks/{task_id}/execute/stream")
async def stream_task_execution(task_id: int):
    async def task_stream():
        # Step 1: Loading task
        yield {
            "event": "status",
            "data": json.dumps({
                "task_id": task_id,
                "status": "loading",
                "message": "Loading task details..."
            })
        }
        await asyncio.sleep(1)

        # Step 2: Validating
        yield {
            "event": "status",
            "data": json.dumps({
                "task_id": task_id,
                "status": "validating",
                "message": "Validating inputs..."
            })
        }
        await asyncio.sleep(1)

        # Step 3: Processing
        yield {
            "event": "status",
            "data": json.dumps({
                "task_id": task_id,
                "status": "processing",
                "message": "Processing task...",
                "progress": 0
            })
        }

        # Simulate processing with progress
        for progress in [25, 50, 75, 100]:
            await asyncio.sleep(1)
            yield {
                "event": "progress",
                "data": json.dumps({
                    "task_id": task_id,
                    "progress": progress
                })
            }

        # Step 4: Complete
        yield {
            "event": "complete",
            "data": json.dumps({
                "task_id": task_id,
                "status": "completed",
                "result": "Task executed successfully"
            })
        }

    return EventSourceResponse(task_stream())
```

**Example 2: Multi-Step Agent Stream**

```python
@app.post("/agent/process/stream")
async def stream_agent_processing(query: str):
    async def agent_stream():
        # Step 1: Understanding query
        yield {
            "event": "thinking",
            "data": json.dumps({
                "step": "understanding",
                "message": "Analyzing your request..."
            })
        }
        await asyncio.sleep(1)

        # Step 2: Planning
        yield {
            "event": "thinking",
            "data": json.dumps({
                "step": "planning",
                "message": "Creating execution plan...",
                "plan": ["Fetch data", "Process data", "Format response"]
            })
        }
        await asyncio.sleep(1)

        # Step 3: Tool calls
        tools = ["database", "api", "formatter"]
        for tool in tools:
            yield {
                "event": "tool",
                "data": json.dumps({
                    "tool": tool,
                    "status": "calling"
                })
            }
            await asyncio.sleep(1)

            yield {
                "event": "tool",
                "data": json.dumps({
                    "tool": tool,
                    "status": "complete",
                    "result": f"{tool} executed"
                })
            }

        # Step 4: Generating response
        response_tokens = ["Here's", " the", " result", ":", " Done!"]
        for token in response_tokens:
            yield {
                "event": "token",
                "data": json.dumps({"token": token})
            }
            await asyncio.sleep(0.2)

        # Step 5: Complete
        yield {
            "event": "complete",
            "data": json.dumps({
                "message": "Processing complete",
                "tokens": len(response_tokens)
            })
        }

    return EventSourceResponse(agent_stream())
```

**Example 3: Progress with Percentage**

```python
@app.get("/tasks/{task_id}/progress/stream")
async def stream_task_progress(task_id: int):
    async def progress_stream():
        steps = [
            ("Initializing", 10),
            ("Loading data", 30),
            ("Processing", 60),
            ("Finalizing", 90),
            ("Complete", 100)
        ]

        for step_name, progress in steps:
            yield {
                "event": "progress",
                "data": json.dumps({
                    "task_id": task_id,
                    "step": step_name,
                    "progress": progress,
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
            await asyncio.sleep(1)

        yield {
            "event": "complete",
            "data": json.dumps({
                "task_id": task_id,
                "final_status": "success"
            })
        }

    return EventSourceResponse(progress_stream())
```

**Key patterns:**

- **Use descriptive event types** - "progress", "tool", "thinking", "complete"
- **Include context in data** - task_id, step names, timestamps
- **Show progress percentages** - Users want to know how long it'll take
- **Enumerate steps** - "Step 1 of 3", helps set expectations
- **Final completion event** - Signals stream is done

## Error Handling in Streams

Errors in streaming endpoints are tricky because the response has already started.

**Problem: Can't Send HTTP Error After Stream Starts**

```python
async def bad_stream():
    yield {"event": "message", "data": json.dumps({"msg": "Starting"})}
    # Response already sent! Can't return 500 error now
    raise Exception("Something went wrong!")
```

Once you've sent the first message, you can't change the HTTP status code. The client already received `200 OK`.

**Solution 1: Send Error as SSE Event**

```python
async def safe_stream():
    try:
        yield {"event": "message", "data": json.dumps({"msg": "Starting"})}
        await asyncio.sleep(1)

        # Simulate error
        if random.random() < 0.3:
            raise ValueError("Random error occurred")

        yield {"event": "message", "data": json.dumps({"msg": "Success"})}
        yield {"event": "complete", "data": json.dumps({"done": True})}

    except Exception as e:
        # Send error as SSE event
        yield {
            "event": "error",
            "data": json.dumps({
                "error": str(e),
                "type": type(e).__name__
            })
        }

@app.get("/stream/safe")
async def safe_streaming():
    return EventSourceResponse(safe_stream())
```

**Client-side error handling:**

```javascript
eventSource.addEventListener('error', (event) => {
    const data = JSON.parse(event.data);
    console.error('Stream error:', data.error);
    eventSource.close();
});
```

**Solution 2: Detect Client Disconnection**

If the client disconnects, stop generating:

```python
from starlette.requests import Request

@app.get("/stream/detect-disconnect")
async def stream_with_disconnect_detection(request: Request):
    async def generate():
        try:
            for i in range(100):
                # Check if client disconnected
                if await request.is_disconnected():
                    print(f"Client disconnected at iteration {i}")
                    break

                yield {
                    "event": "message",
                    "data": json.dumps({"count": i})
                }
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Stream error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(generate())
```

**Why disconnect detection matters:**

- Saves server resources (don't generate data nobody is listening to)
- Prevents memory leaks from abandoned streams
- Cleans up database connections, file handles, etc.

**Solution 3: Timeout Long-Running Streams**

```python
async def timeout_stream():
    start_time = time.time()
    timeout_seconds = 30

    try:
        for i in range(1000):
            # Check timeout
            if time.time() - start_time > timeout_seconds:
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "error": "Stream timeout exceeded",
                        "timeout": timeout_seconds
                    })
                }
                break

            yield {"event": "message", "data": json.dumps({"count": i})}
            await asyncio.sleep(1)

    except Exception as e:
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)})
        }

@app.get("/stream/timeout")
async def streaming_with_timeout():
    return EventSourceResponse(timeout_stream())
```

**Best practices for error handling:**

1. **Always wrap generator in try/except**
2. **Send errors as SSE events** (can't change HTTP status mid-stream)
3. **Detect client disconnection** (save resources)
4. **Implement timeouts** (prevent infinite streams)
5. **Log errors** (for debugging)
6. **Send clear error messages** (include error type and context)

## Complete Streaming Example

A production-ready streaming endpoint with all best practices:

```python
from fastapi import FastAPI, Request, HTTPException
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import asyncio
import json
import time
from datetime import datetime

app = FastAPI()

class TaskRequest(BaseModel):
    task_id: int
    operation: str

@app.post("/tasks/execute/stream")
async def execute_task_stream(task: TaskRequest, request: Request):
    """
    Execute a task with streaming progress updates.

    Events:
    - status: Task status changes
    - progress: Progress percentage (0-100)
    - result: Step results
    - complete: Final completion
    - error: Errors during execution
    """

    async def task_execution_stream():
        start_time = time.time()
        timeout_seconds = 60

        try:
            # Validate task
            yield {
                "event": "status",
                "data": json.dumps({
                    "task_id": task.task_id,
                    "status": "validating",
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
            await asyncio.sleep(0.5)

            # Check disconnect
            if await request.is_disconnected():
                return

            # Simulate task execution steps
            steps = [
                ("Initializing", 10),
                ("Loading data", 25),
                ("Processing", 50),
                ("Analyzing", 75),
                ("Finalizing", 90)
            ]

            for step_name, progress in steps:
                # Check timeout
                if time.time() - start_time > timeout_seconds:
                    yield {
                        "event": "error",
                        "data": json.dumps({
                            "error": "Execution timeout",
                            "timeout_seconds": timeout_seconds
                        })
                    }
                    return

                # Check disconnect
                if await request.is_disconnected():
                    print(f"Client disconnected during step: {step_name}")
                    return

                # Send status
                yield {
                    "event": "status",
                    "data": json.dumps({
                        "task_id": task.task_id,
                        "step": step_name,
                        "progress": progress
                    })
                }

                # Simulate work
                await asyncio.sleep(1)

                # Send result for this step
                yield {
                    "event": "result",
                    "data": json.dumps({
                        "step": step_name,
                        "result": f"{step_name} completed",
                        "progress": progress
                    })
                }

            # Final completion
            yield {
                "event": "complete",
                "data": json.dumps({
                    "task_id": task.task_id,
                    "status": "completed",
                    "duration_seconds": round(time.time() - start_time, 2),
                    "timestamp": datetime.utcnow().isoformat()
                })
            }

        except Exception as e:
            # Send error as SSE event
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": str(e),
                    "type": type(e).__name__,
                    "task_id": task.task_id
                })
            }

    return EventSourceResponse(task_execution_stream())


@app.get("/countdown/{seconds}")
async def countdown_stream(seconds: int, request: Request):
    """Simple countdown stream."""

    async def countdown():
        try:
            for i in range(seconds, 0, -1):
                if await request.is_disconnected():
                    return

                yield {
                    "event": "countdown",
                    "data": json.dumps({"remaining": i})
                }
                await asyncio.sleep(1)

            yield {
                "event": "complete",
                "data": json.dumps({"message": "Countdown finished!"})
            }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(countdown())


@app.get("/agent/think/stream")
async def agent_thinking_stream(query: str, request: Request):
    """Simulate agent thinking process with streaming thoughts."""

    async def thinking_stream():
        try:
            # Initial thought
            yield {
                "event": "thought",
                "data": json.dumps({
                    "type": "initial",
                    "message": f"Analyzing query: {query}"
                })
            }
            await asyncio.sleep(1)

            # Planning
            thoughts = [
                "I need to break this down into steps",
                "First, I'll gather the necessary information",
                "Then I'll process the data",
                "Finally, I'll format a response"
            ]

            for idx, thought in enumerate(thoughts):
                if await request.is_disconnected():
                    return

                yield {
                    "event": "thought",
                    "data": json.dumps({
                        "type": "planning",
                        "step": idx + 1,
                        "total_steps": len(thoughts),
                        "message": thought
                    })
                }
                await asyncio.sleep(0.8)

            # Execution
            yield {
                "event": "status",
                "data": json.dumps({
                    "message": "Executing plan..."
                })
            }
            await asyncio.sleep(1)

            # Response generation (token by token)
            response_text = "Based on my analysis, here is the answer."
            words = response_text.split()

            for word in words:
                if await request.is_disconnected():
                    return

                yield {
                    "event": "token",
                    "data": json.dumps({"token": word + " "})
                }
                await asyncio.sleep(0.1)

            # Complete
            yield {
                "event": "complete",
                "data": json.dumps({
                    "message": "Thinking complete",
                    "thoughts_count": len(thoughts),
                    "response_length": len(response_text)
                })
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(thinking_stream())
```

**Test the complete example:**

```bash
# Terminal 1: Start server
uv run uvicorn main:app --reload

# Terminal 2: Test countdown
curl -N http://localhost:8000/countdown/5

# Terminal 3: Test task execution
curl -N -X POST http://localhost:8000/tasks/execute/stream \
  -H "Content-Type: application/json" \
  -d '{"task_id": 123, "operation": "analyze"}'

# Terminal 4: Test agent thinking
curl -N "http://localhost:8000/agent/think/stream?query=What+is+FastAPI"
```

## Hands-On Exercise

Build a streaming endpoint that simulates a long-running task with progress updates.

**Step 1: Install sse-starlette**

```bash
uv add sse-starlette
```

**Step 2: Create main.py**

```python
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "SSE Streaming API"}

# TODO: Add your streaming endpoint here
```

**Step 3: Create your first streaming endpoint**

Add this endpoint to `main.py`:

```python
@app.get("/stream/hello")
async def stream_hello():
    async def generate():
        messages = ["Hello", "from", "Server-Sent", "Events!"]

        for msg in messages:
            yield {
                "event": "message",
                "data": json.dumps({"text": msg})
            }
            await asyncio.sleep(1)

        yield {
            "event": "complete",
            "data": json.dumps({"done": True})
        }

    return EventSourceResponse(generate())
```

**Step 4: Run the server**

```bash
uv run uvicorn main:app --reload
```

**Step 5: Test with curl**

```bash
curl -N http://localhost:8000/stream/hello
```

You should see:
```
event: message
data: {"text": "Hello"}

event: message
data: {"text": "from"}

event: message
data: {"text": "Server-Sent"}

event: message
data: {"text": "Events!"}

event: complete
data: {"done": true}
```

**Step 6: Test with browser**

Create `test.html`:

```html
<!DOCTYPE html>
<html>
<head><title>SSE Test</title></head>
<body>
    <h1>SSE Test</h1>
    <div id="output"></div>
    <button onclick="startStream()">Start</button>

    <script>
        function startStream() {
            const output = document.getElementById('output');
            output.innerHTML = '<p>Connecting...</p>';

            const es = new EventSource('http://localhost:8000/stream/hello');

            es.addEventListener('message', (e) => {
                const data = JSON.parse(e.data);
                output.innerHTML += `<p>Message: ${data.text}</p>`;
            });

            es.addEventListener('complete', (e) => {
                output.innerHTML += '<p><strong>Complete!</strong></p>';
                es.close();
            });

            es.addEventListener('error', () => {
                output.innerHTML += '<p style="color: red;">Error</p>';
                es.close();
            });
        }
    </script>
</body>
</html>
```

Open in browser and click "Start".

**Step 7: Build a progress tracker**

Add this endpoint:

```python
@app.get("/stream/progress")
async def stream_progress():
    async def generate():
        for i in range(0, 101, 10):
            yield {
                "event": "progress",
                "data": json.dumps({"progress": i})
            }
            await asyncio.sleep(0.5)

        yield {
            "event": "complete",
            "data": json.dumps({"done": True})
        }

    return EventSourceResponse(generate())
```

Test it:
```bash
curl -N http://localhost:8000/stream/progress
```

## Challenge: Build a Progress Tracker

Build a streaming endpoint that simulates an AI agent "thinking" with intermediate thoughts.

**Requirements:**

1. Accept a query parameter: `query`
2. Stream these events in order:
   - Event type "status" - "Analyzing query..."
   - Event type "thought" - 3-5 intermediate thoughts
   - Event type "token" - Response tokens (word by word)
   - Event type "complete" - Final completion

**Starter code:**

```python
@app.get("/agent/stream")
async def agent_stream(query: str):
    async def generate():
        # TODO: Implement the agent thinking stream
        pass

    return EventSourceResponse(generate())
```

**Solution:**

```python
@app.get("/agent/stream")
async def agent_stream(query: str):
    async def generate():
        # Status
        yield {
            "event": "status",
            "data": json.dumps({"message": "Analyzing query..."})
        }
        await asyncio.sleep(1)

        # Thoughts
        thoughts = [
            "Breaking down the problem",
            "Searching for relevant information",
            "Processing the data",
            "Formulating a response"
        ]

        for idx, thought in enumerate(thoughts):
            yield {
                "event": "thought",
                "data": json.dumps({
                    "step": idx + 1,
                    "total": len(thoughts),
                    "thought": thought
                })
            }
            await asyncio.sleep(0.8)

        # Token generation
        response = f"Based on your query about '{query}', here is my response."
        words = response.split()

        for word in words:
            yield {
                "event": "token",
                "data": json.dumps({"token": word + " "})
            }
            await asyncio.sleep(0.1)

        # Complete
        yield {
            "event": "complete",
            "data": json.dumps({"done": True, "query": query})
        }

    return EventSourceResponse(generate())
```

**Test your solution:**

```bash
curl -N "http://localhost:8000/agent/stream?query=What+is+SSE"
```

**Expected output:**

```
event: status
data: {"message": "Analyzing query..."}

event: thought
data: {"step": 1, "total": 4, "thought": "Breaking down the problem"}

event: thought
data: {"step": 2, "total": 4, "thought": "Searching for relevant information"}

... (more thoughts)

event: token
data: {"token": "Based "}

event: token
data: {"token": "on "}

... (more tokens)

event: complete
data: {"done": true, "query": "What is SSE"}
```

**Bonus challenges:**

1. Add error handling (try/except)
2. Detect client disconnection
3. Add progress percentages
4. Include timestamps in events
5. Implement a timeout (max 30 seconds)

## Common Mistakes

**Mistake 1: Using `return` instead of `yield`**

```python
# ❌ WRONG - Returns once, not a generator
async def bad_generator():
    return {"data": "Hello"}  # Not a stream!

# ✅ CORRECT - Yields multiple times
async def good_generator():
    yield {"event": "message", "data": json.dumps({"text": "Hello"})}
    yield {"event": "message", "data": json.dumps({"text": "World"})}
```

**Mistake 2: Forgetting `json.dumps()` for data**

```python
# ❌ WRONG - data must be a string
yield {
    "event": "message",
    "data": {"text": "Hello"}  # Dict, not string!
}

# ✅ CORRECT - Convert to JSON string
yield {
    "event": "message",
    "data": json.dumps({"text": "Hello"})
}
```

**Mistake 3: Using `time.sleep()` instead of `await asyncio.sleep()`**

```python
# ❌ WRONG - Blocks the entire event loop!
async def bad_sleep():
    yield {"event": "message", "data": json.dumps({"text": "Hello"})}
    time.sleep(1)  # BLOCKS everything!
    yield {"event": "message", "data": json.dumps({"text": "World"})}

# ✅ CORRECT - Non-blocking async sleep
async def good_sleep():
    yield {"event": "message", "data": json.dumps({"text": "Hello"})}
    await asyncio.sleep(1)  # Non-blocking!
    yield {"event": "message", "data": json.dumps({"text": "World"})}
```

**Mistake 4: Not closing connections**

```python
# ❌ WRONG - Leaks connections
async def infinite_stream():
    while True:  # Never ends!
        yield {"event": "message", "data": json.dumps({"count": 1})}
        await asyncio.sleep(1)

# ✅ CORRECT - Finite stream with completion
async def finite_stream():
    for i in range(10):
        yield {"event": "message", "data": json.dumps({"count": i})}
        await asyncio.sleep(1)
    yield {"event": "complete", "data": json.dumps({"done": True})}
```

**Mistake 5: Not handling client disconnection**

```python
# ❌ WRONG - Continues generating even if client disconnected
async def no_disconnect_check():
    for i in range(1000):
        yield {"event": "message", "data": json.dumps({"count": i})}
        await asyncio.sleep(1)
    # Wastes resources if client left!

# ✅ CORRECT - Check for disconnection
from starlette.requests import Request

@app.get("/stream")
async def with_disconnect_check(request: Request):
    async def generate():
        for i in range(1000):
            if await request.is_disconnected():
                print("Client disconnected, stopping stream")
                break
            yield {"event": "message", "data": json.dumps({"count": i})}
            await asyncio.sleep(1)

    return EventSourceResponse(generate())
```

**Mistake 6: Raising exceptions without catching**

```python
# ❌ WRONG - Crashes the stream
async def bad_error_handling():
    yield {"event": "message", "data": json.dumps({"text": "Starting"})}
    raise ValueError("Something broke!")  # Stream crashes!

# ✅ CORRECT - Send error as SSE event
async def good_error_handling():
    try:
        yield {"event": "message", "data": json.dumps({"text": "Starting"})}
        # ... work ...
        if error_condition:
            raise ValueError("Something broke!")
    except Exception as e:
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)})
        }
```

**Mistake 7: Testing SSE with Swagger UI**

```python
@app.get("/stream")
async def stream():
    return EventSourceResponse(generate())
```

⚠️ **Swagger UI doesn't support streaming!**

It will:
- Wait for the entire stream to complete
- Show all data at once
- Lose SSE formatting

**✅ Test with:**
- `curl -N`
- Browser `EventSource`
- Custom HTML test page

**Mistake 8: Not setting proper event types**

```python
# ❌ WRONG - All events have type "message" (default)
yield {"data": json.dumps({"text": "Hello"})}
yield {"data": json.dumps({"text": "World"})}
# Client can't distinguish event types!

# ✅ CORRECT - Use descriptive event types
yield {"event": "status", "data": json.dumps({"text": "Starting"})}
yield {"event": "progress", "data": json.dumps({"percent": 50})}
yield {"event": "complete", "data": json.dumps({"done": True})}
```

**Mistake 9: Forgetting to import required modules**

```python
# ❌ WRONG - Missing imports
@app.get("/stream")
async def stream():
    async def generate():
        yield {"data": json.dumps({"count": 1})}  # Where's json?
    return EventSourceResponse(generate())  # Where's EventSourceResponse?

# ✅ CORRECT - Import everything needed
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

@app.get("/stream")
async def stream():
    async def generate():
        yield {"event": "message", "data": json.dumps({"count": 1})}
        await asyncio.sleep(1)
    return EventSourceResponse(generate())
```

**Mistake 10: Not handling CORS for browser clients**

```python
# ❌ WRONG - Browser can't connect (CORS error)
app = FastAPI()

@app.get("/stream")
async def stream():
    return EventSourceResponse(generate())
```

If testing from browser on different origin:
```
Access to fetch at 'http://localhost:8000/stream' from origin
'http://localhost:3000' has been blocked by CORS policy
```

```python
# ✅ CORRECT - Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/stream")
async def stream():
    return EventSourceResponse(generate())
```

## Key Points

- SSE enables real-time streaming over HTTP with simple text-based protocol
- Use `sse-starlette` for FastAPI: `uv add sse-starlette`
- Async generators (`async def` + `yield`) are the foundation of streaming
- SSE data must be JSON string: use `json.dumps()`
- Use `await asyncio.sleep()` NOT `time.sleep()` (non-blocking)
- `EventSourceResponse` wraps generator and handles SSE formatting
- SSE is better than WebSockets for one-directional server-to-client streaming
- Browser has built-in `EventSource` API for consuming SSE streams
- Swagger UI doesn't support SSE - test with curl, browser, or custom HTML
- Always handle errors as SSE events (can't change HTTP status mid-stream)
- Detect client disconnection to save resources: `await request.is_disconnected()`
- Use descriptive event types: "progress", "complete", "error", "token"
- SSE is perfect for agent APIs: show thinking, tool calls, LLM tokens in real-time
- First byte matters more than last byte - streaming improves perceived performance

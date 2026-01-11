# Prompt: Build a Task Management API

I need a Task Management API built with FastAPI. Can you help me create it from scratch? 

## What I Need

I want an API where I can manage tasks. Each task should have:
- A title (required)
- A description (optional)
- A status that can be "pending", "in_progress", or "completed" (starts as "pending")
- An ID and timestamps for when it was created and updated

## What Should It Do?

I need to be able to:
1. Create new tasks
2. See all my tasks (and filter by status if I want)
3. Get a single task by its ID
4. Update a task (change its title, description, or status)
5. Delete a task

The data should be saved in a database so it doesn't disappear when I restart the server.

## How I Want It Built

Please use:
- FastAPI for the API
- SQLModel for the database (I heard it's good for combining Pydantic and SQLAlchemy)
- pytest for testing (I want good test coverage)
- Follow test-driven development - write tests first, then make them pass

## Make It Production Ready

I want:
- Proper error handling (like 404 when a task doesn't exist)
- Input validation (don't let me create tasks without 
titles)
- All the code to follow FastAPI best practices
- Tests that cover all the functionality
- A README explaining how to set it up and use it

## Database Setup

I prefer to use a managed PostgreSQL database like Neon (it's free and easy), but you can set it up however makes sense. Just make sure it works and the connection string goes in an `.env` file.

Build this project from scratch in a folder called `task-management-api`. Make sure everything works and I can run it with `uv run uvicorn main:app --reload`.

That's it! Use your FastAPI skill to build this the right way.

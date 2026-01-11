#!/usr/bin/env python3
"""
FastAPI Project Scaffolding Script

Creates a new FastAPI project with a standard directory structure and boilerplate files.

Usage:
    python create_project.py <project_name> [--with-docker] [--with-tests]
"""

import argparse
import os
import sys
from pathlib import Path


def create_project_structure(project_name, with_docker=False, with_tests=False):
    """Create the project directory structure and files."""
    base_path = Path(project_name)

    if base_path.exists():
        print(f"Error: Directory '{project_name}' already exists!")
        sys.exit(1)

    # Create directory structure
    directories = [
        base_path / "app",
        base_path / "app" / "routers",
        base_path / "app" / "models",
        base_path / "app" / "schemas",
        base_path / "app" / "services",
        base_path / "app" / "dependencies",
    ]

    if with_tests:
        directories.append(base_path / "tests")

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        # Create __init__.py files
        if "app" in str(directory):
            (directory / "__init__.py").touch()

    # Create main.py
    main_content = '''from fastapi import FastAPI

app = FastAPI(
    title="''' + project_name + ''' API",
    description="API built with FastAPI",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {"message": "Welcome to ''' + project_name + ''' API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
'''

    (base_path / "app" / "main.py").write_text(main_content, encoding='utf-8')

    # Create requirements.txt
    requirements = '''fastapi[standard]>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
'''

    if with_tests:
        requirements += '''pytest>=7.0.0
httpx>=0.24.0
'''

    (base_path / "requirements.txt").write_text(requirements, encoding='utf-8')

    # Create .env.example
    env_example = '''# Application Settings
APP_NAME=''' + project_name + '''
DEBUG=True
API_VERSION=1.0.0

# Server Settings
HOST=0.0.0.0
PORT=8000
'''

    (base_path / ".env.example").write_text(env_example, encoding='utf-8')

    # Create .gitignore
    gitignore = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# FastAPI
.env
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db
'''

    (base_path / ".gitignore").write_text(gitignore, encoding='utf-8')

    # Create README.md
    readme = f'''# {project_name}

FastAPI project generated with the FastAPI skill.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and configure as needed:
```bash
cp .env.example .env
```

## Running the Application

### Development Mode
```bash
fastapi dev app/main.py
```

Or with uvicorn directly:
```bash
uvicorn app.main:app --reload
```

### Production Mode
```bash
fastapi run app/main.py
```

Or with uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json

## Project Structure

```
{project_name}/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── routers/             # API route handlers
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── dependencies/        # Dependency injection
├── tests/                   # Test files
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```
'''

    (base_path / "README.md").write_text(readme, encoding='utf-8')

    # Create Docker files if requested
    if with_docker:
        dockerfile = '''FROM python:3.11-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["fastapi", "run", "app/main.py", "--port", "80"]
'''

        (base_path / "Dockerfile").write_text(dockerfile, encoding='utf-8')

        docker_compose = f'''version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:80"
    environment:
      - APP_NAME={project_name}
      - DEBUG=False
    volumes:
      - ./app:/code/app
'''

        (base_path / "docker-compose.yml").write_text(docker_compose, encoding='utf-8')

    # Create test files if requested
    if with_tests:
        test_main = '''from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
'''

        (base_path / "tests" / "test_main.py").write_text(test_main, encoding='utf-8')
        (base_path / "tests" / "__init__.py").touch()

        pytest_ini = '''[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
'''

        (base_path / "pytest.ini").write_text(pytest_ini, encoding='utf-8')

    print(f"Created FastAPI project: {project_name}")
    print(f"\nNext steps:")
    print(f"  cd {project_name}")
    print(f"  pip install -r requirements.txt")
    print(f"  fastapi dev app/main.py")
    print(f"\nAPI docs will be available at: http://localhost:8000/docs")


def main():
    parser = argparse.ArgumentParser(
        description="Create a new FastAPI project with standard structure"
    )
    parser.add_argument(
        "project_name",
        help="Name of the project to create"
    )
    parser.add_argument(
        "--with-docker",
        action="store_true",
        help="Include Dockerfile and docker-compose.yml"
    )
    parser.add_argument(
        "--with-tests",
        action="store_true",
        help="Include test directory and pytest configuration"
    )

    args = parser.parse_args()

    create_project_structure(
        args.project_name,
        with_docker=args.with_docker,
        with_tests=args.with_tests
    )


if __name__ == "__main__":
    main()

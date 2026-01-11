# FastAPI Hello World

A minimal FastAPI application to get started quickly.

## Installation

```bash
pip install -r requirements.txt
```

## Running

### Development mode (with auto-reload)
```bash
fastapi dev main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload
```

### Production mode
```bash
fastapi run main.py
```

## API Documentation

Once running, visit:
- Interactive docs (Swagger UI): http://localhost:8000/docs
- Alternative docs (ReDoc): http://localhost:8000/redoc
- OpenAPI schema: http://localhost:8000/openapi.json

## Endpoints

- `GET /` - Hello World message
- `GET /health` - Health check endpoint
- `GET /items/{item_id}` - Example path parameter with optional query param

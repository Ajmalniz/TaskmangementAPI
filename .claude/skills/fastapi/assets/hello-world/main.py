from fastapi import FastAPI

app = FastAPI(
    title="Hello World API",
    description="A simple FastAPI application",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

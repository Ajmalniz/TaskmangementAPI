from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.routers import items
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Production-ready FastAPI application",
    version=settings.version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(items.router, prefix="/api/v1", tags=["items"])


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.app_name}"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.version}

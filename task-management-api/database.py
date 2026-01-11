"""Database connection and session management."""
from sqlmodel import create_engine, Session
from config import get_settings

settings = get_settings()

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    echo=True if settings.environment == "development" else False,
    pool_pre_ping=True,  # Verify connections before using
)


def get_session():
    """Dependency for getting a database session."""
    with Session(engine) as session:
        yield session

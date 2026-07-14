"""
Test database setup.

Sets DATABASE_URL and SECRET_KEY env vars before any app module is imported,
then replaces the production engine with an in-memory SQLite engine backed by
StaticPool so all sessions share the same database.
"""
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.database as _db
from app.database import Base

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_db.engine = _engine
_db.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

# Import models so SQLAlchemy knows about every table before create_all.
import app.models  # noqa: F401 — side-effect import registers all ORM classes


@pytest.fixture()
def db():
    """Create all tables, yield a session, then drop everything.

    Each test gets a completely empty database.
    """
    Base.metadata.create_all(bind=_engine)
    session = _db.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def client(db):
    """TestClient wired to the same `db` session used by test setup helpers.

    Overriding get_db to yield the *same* session (rather than a fresh one)
    means fixtures created via db.flush() in a test are visible to the
    request handler without needing an intermediate commit.
    """
    from fastapi.testclient import TestClient
    from app.database import get_db
    from app.main import app

    def _get_db():
        yield db

    app.dependency_overrides[get_db] = _get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)

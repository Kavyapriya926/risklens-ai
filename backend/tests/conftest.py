"""Test fixtures and configuration.

Strategy: we create a shared SQLite file (risklens_test.db) for the test
session. The DATABASE_URL env var is set before any app imports so that
SQLAlchemy's engine points to it. All tables are created once. The FastAPI
dependency override + init_db patch ensure every endpoint uses this DB.
"""
import sys
import os
import tempfile
from pathlib import Path

# ── Set env vars BEFORE any app module is imported ──────────────────────────
DB_PATH = Path(__file__).parent.parent / "risklens_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH}"
os.environ["MODEL_DIR"] = str(Path(__file__).parent.parent / "models")
os.environ["DATA_DIR"] = str(Path(__file__).parent.parent / "data")

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_ENGINE = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables once for the whole test session."""
    from app.database import Base
    from app.models import transaction, investigation, audit  # noqa
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)
    try:
        DB_PATH.unlink(missing_ok=True)
    except PermissionError:
        pass  # Windows may hold the file — safe to leave it


@pytest.fixture()
def db_session(setup_test_db):
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(setup_test_db):
    """FastAPI test client wired to the test DB."""
    from app.main import app
    from app.database import get_db
    import app.database as db_mod

    def override_get_db():
        s = TestSession()
        try:
            yield s
        finally:
            s.close()

    # Patch get_db dependency
    app.dependency_overrides[get_db] = override_get_db

    # Patch init_db so lifespan event uses the test engine
    _orig_init = db_mod.init_db

    def _test_init():
        from app.models import transaction, investigation, audit  # noqa
        db_mod.Base.metadata.create_all(bind=TEST_ENGINE)

    db_mod.init_db = _test_init

    from fastapi.testclient import TestClient
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()
    db_mod.init_db = _orig_init


@pytest.fixture(scope="session")
def trained_models():
    """Train models once per session."""
    model_dir = Path(tempfile.mkdtemp(prefix="rl_test_"))

    from data.generate_data import generate_synthetic_dataset
    from app.ml.pipeline import train_models
    df = generate_synthetic_dataset(n_samples=2000, fraud_rate=0.08, random_state=0)
    meta = train_models(df, str(model_dir))
    yield meta

    import shutil
    shutil.rmtree(model_dir, ignore_errors=True)

"""Shared pytest fixtures for the backend test suite.

The backend (src/celiacwriteoff/backend/) uses flat, bare imports like
`import db` and `from main import app` -- these resolve because
`pythonpath = ["src/celiacwriteoff/backend"]` in pyproject.toml's
[tool.pytest.ini_options] puts that directory on sys.path for pytest.
"""

import sqlite3
from collections.abc import Iterator

import db
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def test_db_path(tmp_path, monkeypatch):
    """Point db.DB_PATH at a fresh temp sqlite file and initialize its schema.

    Patching db.DB_PATH (not storage.DB_PATH) matters: db.py did
    `from storage import DB_PATH`, which bound its own name at import time,
    so patching storage's copy after the fact would not affect db.py.
    This must run before the TestClient fixture below constructs/enters the
    app, since main.py's lifespan calls db.init_db() on startup -- if this
    patch happened after that, the real dev database would get touched.
    """
    path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    db.init_db()
    return path


@pytest.fixture
def client(test_db_path) -> Iterator[TestClient]:
    """A TestClient wired to the isolated temp database for this test."""

    def override_get_db() -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(test_db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[db.get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _no_external_services(monkeypatch):
    """Make sure CAPTCHA/email bypass paths engage regardless of the shell env.

    recaptcha.py and email_service.py already skip real verification/sending
    when these vars are unset -- this just guarantees that behavior even if
    a developer's shell happens to export them.
    """
    monkeypatch.delenv("RECAPTCHA_SECRET_KEY", raising=False)
    monkeypatch.delenv("SENDGRID_API_KEY", raising=False)
    monkeypatch.delenv("RESET_EMAIL_FROM", raising=False)

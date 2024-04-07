from collections.abc import Generator
from pathlib import Path

import pytest
from dramatiq import Worker
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.api import app
from app.db import create_db_and_tables, engine
from app.models import Document, DocumentUnique
from app.worker import broker

"""
    Used to set up fixtures for testing and potentially more setups/teardowns.
    For this specific service, file preparation and cleanup could and should be done via setups/teardowns here.
"""

TEST_FILES_PATH = Path("app/tests/test_input_files")


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        create_db_and_tables()
        yield session
        statement = delete(Document)
        session.execute(statement)
        statement = delete(DocumentUnique)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def stub_broker():
    broker.flush_all()
    return broker


@pytest.fixture()
def stub_worker():
    worker = Worker(broker, worker_timeout=100)
    worker.start()
    yield worker
    worker.stop()

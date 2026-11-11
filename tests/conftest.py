from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "storage", main.MovieStorage(tmp_path / "movies.db"))
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture
def sample_upload():
    path = Path(__file__).resolve().parents[1] / "fixtures" / "sample_movies.csv"
    return {"file": (path.name, path.read_bytes(), "text/csv")}

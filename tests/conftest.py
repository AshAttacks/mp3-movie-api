from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import main
from src import MovieCache, MovieStorage

@pytest.fixture
def client(test_storage, monkeypatch):
    monkeypatch.setattr(main, "storage", test_storage)
    monkeypatch.setattr(main, "cache", MovieCache())
    with TestClient(main.app) as test_client:
        yield test_client



@pytest.fixture
def sample_upload():
    path = Path(__file__).resolve().parents[1] / "fixtures" / "sample_movies.csv"
    return {"file": (path.name, path.read_bytes(), "text/csv")}


@pytest.fixture
def test_storage(tmp_path):
    return MovieStorage(tmp_path / "test_movies.db")

@pytest.fixture
def sample_csv_bytes():
    return (Path("fixtures") / "sample_movies.csv").read_bytes()


@pytest.fixture
def uploaded_movies(client, sample_csv_bytes):
    response = client.post(
        "/upload",
        files={"file": ("sample_movies.csv", sample_csv_bytes, "text/csv")}
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def processing_body():
    return {
        "validation": {
            "required_columns": ["title", "release_year", "rating", "genre"],
            "numeric_columns": ["release_year", "rating"]
        },
        "processing": {
            "remove_duplicates": True,
            "missing": {"enabled": True, "axis": "rows"},
            "outliers": {
                "enabled": True,
                "columns": ["rating"],
                "method": "iqr",
                "threshold": 1.5
            }
        }
    }

def test_movies_persist(client, test_storage, uploaded_movies):
    # TODO: create another MovieStorage pointing to test_storage.db_path.
    # Use that object to get the movies and count them.
    # Check 20 rows, all four DataFrame columns, and the original title order.
    # Compare IDs from that object's select_columns() with GET /movies?limit=100.
    # Both should return IDs 1 through 20 in row order.
    pass


def test_cache_and_processing(client, uploaded_movies, processing_body):
    # TODO 1: GET /movies with limits 100 and 1.
    # Check 200 and that main.cache.get(limit) equals each response body.

    # TODO 2: repeat limit=100 and check the same response.

    # TODO 3: POST /movies/process using json=processing_body.
    # Check 200, zero validation removals, and the 20 -> 16 cleaning report.
    # Confirm both old cache entries are None.

    # TODO 4: retrieve again; check total_rows=16 and titles Movie A through Movie P, in order.
    # Check IDs 1 through 16 in the retrieved records.
    # Check that the new response is cached.
    pass


def test_cache_hit_skips_database(client, uploaded_movies, monkeypatch):
    # TODO 1: GET /movies with limit=100 to populate the cache.
    # Assert 200 and keep the response for comparison.

    # TODO 2: Use monkeypatch to replace main.storage.select_columns()
    # and main.storage.count_movies() with a function that fails the test
    # if either method is called.

    # TODO 3: Repeat the same GET request.
    # Assert 200 and the same response body as the first request.
    pass
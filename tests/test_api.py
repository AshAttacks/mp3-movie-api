import pytest

import main
from src import MovieStorage


def test_upload_retrieve_and_replace(client, sample_upload, monkeypatch):
    response = client.post("/upload", files=sample_upload)
    assert response.status_code == 200
    assert response.json() == {
        "filename": "sample_movies.csv",
        "rows": 20,
        "columns": 4,
        "column_names": ["title", "release_year", "rating", "genre"],
    }
    expected = {
        "data": [
            {"id": 1, "title": "Movie A", "release_year": 2020, "rating": 8.0, "genre": "Drama"},
            {"id": 2, "title": "Movie B", "release_year": 2021, "rating": 8.5, "genre": "Comedy"},
        ],
        "total_rows": 20,
    }
    assert client.get("/movies?limit=2").json() == expected
    monkeypatch.setattr(main, "storage", main.MovieStorage(main.storage.db_path))
    assert client.get("/movies?limit=2").json() == expected
    assert client.post("/upload", files=sample_upload).status_code == 200
    assert client.get("/movies?limit=2").json() == expected


def test_search(client, sample_upload, caplog):
    caplog.set_level("DEBUG")
    assert client.post("/upload", files=sample_upload).status_code == 200
    url = "/movies/search?min_rating=8.5&limit=2"
    assert client.get(url).json() == [
        {"id": 4, "title": "Movie C"},
        {"id": 2, "title": "Movie B"},
    ]
    assert client.get(url + "&columns=title&columns=rating").json() == [
        {"id": 4, "title": "Movie C", "rating": 9.0},
        {"id": 2, "title": "Movie B", "rating": 8.5},
    ]
    assert ("src.storage", 10, "Stored movies in SQLite: rows=20") in caplog.record_tuples
    assert (
        "main", 20, "Uploaded movies: filename=sample_movies.csv, rows=20"
    ) in caplog.record_tuples
    assert (
        "main", 20, "Queried movies: columns=['title', 'rating'], min_rating=8.5, returned_rows=2"
    ) in caplog.record_tuples
    assert client.get("/movies/search?columns=unknown").status_code == 400
    assert client.get("/movies/search?min_rating=10").json() == []


def test_invalid_upload_and_health(client):
    for name, data in [
        ("movies.txt", b"title,release_year,rating,genre\nA,2020,8,Drama"),
        ("movies.csv", b"title,release_year,rating,genre\n"),
        ("movies.csv", b"title,rating\nA,8"),
    ]:
        assert client.post("/upload", files={"file": (name, data)}).status_code == 400
    assert client.get("/health").status_code == 200


def test_process_movies(client, sample_upload):
    assert client.get("/movies").json() == {"data": [], "total_rows": 0}
    assert client.post("/movies/process", json={}).status_code == 400
    assert client.post("/upload", files=sample_upload).status_code == 200
    response = client.post("/movies/process", json={})
    assert response.status_code == 200
    assert response.json() == {
        "validation_rows_removed": 0,
        "cleaning_report": {
            "rows_before": 20,
            "rows_after": 18,
            "rows_removed": 2,
            "columns_before": 4,
            "columns_after": 4,
            "columns_removed": 0,
        },
    }
    assert client.get("/movies").json()["total_rows"] == 18


def test_movies_persist(client, test_storage, uploaded_movies):
    # TODO: create another MovieStorage pointing to test_storage.db_path.
    storage = MovieStorage(test_storage.db_path)
    # Use that object to get the movies and count them.
    movies = storage.get()
    # Check 20 rows, all four DataFrame columns, and the original title order.
    assert storage.count_movies() == 20
    assert len(movies) == 20
    assert movies.columns.tolist() == ["title", "release_year", "rating", "genre"]

    assert movies['title'].tolist() == [
        "Movie A", "Movie B", "Movie B", "Movie C", "Movie D", "Movie D",
        "Movie E", "Movie F", "Movie G", "Movie H", "Movie I", "Movie J",
        "Movie K", "Movie L", "Movie M", "Movie N", "Movie O", "Movie P",
        "Movie Q", "Movie R",
    ]

    # Compare IDs from that object's select_columns() with GET /movies?limit=100.
    movies2 = storage.select_columns(['title'], 100)
    response = client.get(
        "/movies?limit=100",
    )
    assert response.status_code == 200
    # Both should return IDs 1 through 20 in row order.
    expected_ids = list(range(1,21))
    keys = [d['id'] for d in movies2]
    keys2 = [d['id'] for d in response.json()['data']]
    assert keys == expected_ids
    assert keys2 == expected_ids


def test_cache_and_processing(client, uploaded_movies, processing_body):
    # TODO 1: GET /movies with limits 100 and 1.
    # Check 200 and that main.cache.get(limit) equals each response body.
    response1 = client.get(
        "/movies?limit=100",
    )

    assert response1.status_code == 200
    assert main.cache.get(100) == response1.json()

    response2 = client.get(
        "/movies?limit=1",
    )

    assert response2.status_code == 200
    assert main.cache.get(1) == response2.json()

    # TODO 2: repeat limit=100 and check the same response.
    response3 = client.get(
        "/movies?limit=100",
    )

    assert response3.status_code == 200
    assert response3.json() == response1.json()
    assert main.cache.get(100) == response3.json()

    # TODO 3: POST /movies/process using json=processing_body.
    # Check 200, zero validation removals, and the 20 -> 16 cleaning report.
    # Confirm both old cache entries are None.

    response4 = client.post(
        "/movies/process",
        json=processing_body
    )

    result = response4.json()
    assert response4.status_code == 200
    assert result["validation_rows_removed"] == 0
    assert result["cleaning_report"]["rows_before"] == 20
    assert result["cleaning_report"]["rows_after"] == 16
    assert main.cache.get(100) is None
    assert main.cache.get(1) is None

    # TODO 4: retrieve again; check total_rows=16 and titles Movie A through Movie P, in order.
    # Check IDs 1 through 16 in the retrieved records.
    # Check that the new response is cached.

    response5 = client.get(
        "/movies?limit=100"
    )
    assert response5.status_code == 200
    result = response5.json()
    assert result["total_rows"] == 16
    ids = [movie["id"] for movie in result["data"]]
    assert ids == list(range(1, 17))
    titles = [movie["title"] for movie in result["data"]]
    assert titles == [
        "Movie A", "Movie B", "Movie C", "Movie D",
        "Movie E", "Movie F", "Movie G", "Movie H", "Movie I", "Movie J",
        "Movie K", "Movie L", "Movie M", "Movie N", "Movie O", "Movie P"
    ]
    assert main.cache.get(100) == result


def test_cache_hit_skips_database(client, uploaded_movies, monkeypatch):
    # TODO 1: GET /movies with limit=100 to populate the cache.
    # Assert 200 and keep the response for comparison.
    response1 = client.get(
        "/movies?limit=100"
    )
    assert response1.status_code == 200
    # TODO 2: Use monkeypatch to replace main.storage.select_columns()
    # and main.storage.count_movies() with a function that fails the test
    # if either method is called.
    def fail_if_called(*args, **kwargs):
        pytest.fail("A cache hit should not query the database")

    monkeypatch.setattr(main.storage, "select_columns", fail_if_called)
    monkeypatch.setattr(main.storage, "count_movies", fail_if_called)

    # TODO 3: Repeat the same GET request.
    # Assert 200 and the same response body as the first request.
    response2 = client.get(
        "/movies?limit=100"
    )
    assert response2.status_code == 200
    assert response2.json() == response1.json()

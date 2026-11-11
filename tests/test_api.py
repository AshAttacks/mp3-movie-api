import main


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

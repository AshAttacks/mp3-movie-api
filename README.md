## Cleaning Data API Description:

This API lets users upload movie CSVs, configure validation and cleaning, and
retrieve the processed rows. `main.py` handles uploads and uses `src/storage.py`
to save the movie collection in SQLite. Reusable validation and cleaning
functions live in `data_pipeline/` and support removing duplicates, handling
missing values, and removing outliers. After processing, the API saves the
cleaned rows and returns a JSON report summarizing the changes. `src/cache.py`
caches `GET /movies` responses by row limit so repeated requests can reuse the
cached results. Uploading or processing movies clears the cache so the next
request reads the updated rows from SQLite.

## Data Movement:

1. Upload a CSV file with `POST /upload` and receive the filename and row and column details
2. Submit validation and cleaning settings to `POST /movies/process`
3. The API validates and cleans the movies based on your config, then updates the stored rows in SQLite
4. The API returns a cleaning report as JSON
5. Retrieve the stored rows with `GET /movies`

## Run the API:

From the `mp3-movie-api/` folder:

```bash
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Run pytest file:

```bash
python -m pytest tests -v
```

## Sample Processing Request

With the API running, upload the sample CSV and process it with the default settings.

The processing request will return HTTP 200. The expected result: removes two duplicate rows 
and leaving 18 movies.

```json
{
  "validation_rows_removed": 0,
  "cleaning_report": {
    "rows_before": 20,
    "rows_after": 18,
    "rows_removed": 2,
    "columns_before": 4,
    "columns_after": 4,
    "columns_removed": 0
  }
}
```

## Data Organization

```text
mp3-movie-api/
├── .gitignore
├── README.md
├── main.py
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── cache.py              
│   ├── database.py           
│   ├── middleware.py
│   ├── models.py
│   ├── storage.py           
│   └── utils.py
├── data_pipeline/
│   ├── __init__.py
│   ├── data_loaders.py
│   ├── data_output.py
│   ├── data_processor.py
│   ├── data_validator.py
│   └── utils.py
├── fixtures/
│   └── sample_movies.csv     
└── tests/
    ├── conftest.py           
    └── test_api.py         
```

import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src import (DatasetInfo, MovieStorage, HealthResponse, MovieCache,
                 setup_logging, ProcessingReport, ProcessConfig, log_requests,
                 MovieUploadInfo, MovieDataResponse, MovieProcessingReport)

from src.storage import MOVIE_COLUMNS

from data_pipeline import create_cleaning_report, process_data, validate_dataframe

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
app.middleware("http")(log_requests)
storage = MovieStorage()
cache = MovieCache()

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return HealthResponse(status='ok', version='1.0.0')

# TODO REMOVE THIS ONE AFTER DONE WITH UPDATED UPLOAD
@app.post("/upload", response_model=DatasetInfo)
async def upload_dataset(file: UploadFile = File(...)):
    """Read and store a CSV upload."""
    suffix = Path(file.filename or '').suffix.lower()
    if suffix != '.csv':
        logger.warning(f'Unsupported file format: {suffix}')
        raise HTTPException(400, 'Unsupported or unreadable CSV upload')

    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
        logger.warning('Unable to read CSV file')
        raise HTTPException(400, 'Unsupported or unreadable CSV upload')

    dataset_id = storage.save(df, file.filename)
    metadata = storage.get_metadata(dataset_id)

    filename = metadata['filename']
    rows = metadata['rows']
    columns = metadata['columns']
    column_names = metadata['column_names']

    logger.info(f'Dataset ID: {dataset_id} | Filename: {filename} | Rows: {rows}')

    return DatasetInfo(id=dataset_id, filename=filename, rows=rows, columns=columns, column_names=column_names)


@app.post("/upload", response_model=MovieUploadInfo)
async def upload_movies(file: UploadFile = File(...)):
    # TODO 1: Keep MP2's .csv check, await file.read(), and CSV parsing.
    # Raise HTTPException with status 400 for an unsupported extension or an expected parsing failure.
    suffix = Path(file.filename or '').suffix.lower()
    if suffix != '.csv':
        logger.warning(f'Unsupported file format: {suffix}')
        raise HTTPException(400, 'Unsupported or unreadable CSV upload')

    # TODO 2: Quick validation before saving:
    # Require exactly MOVIE_COLUMNS
    # Require at least one data row (hint: Use if df.empty: to check for an empty DataFrame).
    # Raise HTTPException with status 400 if these checks fail.
    # Reorder the columns to match MOVIE_COLUMNS.

    # TODO 3: Call storage.save(df) to replace the current collection.
    # Log the filename and saved row count at INFO.
    # Return filename, rows, columns, and column_names for this upload.
    pass

# TODO DELETE AFTER DONE UPDATING NEW GET FUNCTION
@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, limit: int = Query(default=100, ge=1)):
    """Return up to limit rows from a stored dataset."""
    df = storage.get(dataset_id)
    if df is None:
        logger.warning('Dataset not found')
        raise HTTPException(404,' Dataset ID not found')

    records = json.loads(df.head(limit).to_json(orient='records'))
    logger.info(f'Returned dataset id: {dataset_id} | Returned Rows {len(df.head(limit))}')
    return {
        'id': dataset_id,
        'data': records,
        'total_rows': len(df),
    }

@app.get("/movies", response_model=MovieDataResponse)
def get_movies(limit: int = Query(default=100, ge=1)):
    # TODO: Use MovieStorage methods to retrieve up to limit rows and count the total number of stored movies.
    # Return {"data": ..., "total_rows": ...}.
    # If empty, return {"data": [], "total_rows": 0}.
    # Log the row count at INFO.
    pass

# TODO DELETE AFTER UPDATE
@app.post(
    "/datasets/{dataset_id}/process",
    response_model=ProcessingReport
)
def process_dataset(dataset_id: int, config: ProcessConfig):
    """Validate and process a stored dataset using MP1 functions."""
    # TODO: retrieve, validate, process, report, update, and return.

    df = storage.get(dataset_id)
    if df is None:
        raise HTTPException(404,' Dataset ID not found')

    config = config.model_dump()

    df_original = df.copy()

    # Verify Numeric in Columns
    dfcols = df.columns.tolist()
    numeric_cols = config.get('validation', {}).get('numeric_columns', {})

    for col in numeric_cols:
        if col not in dfcols:
            raise HTTPException(400, f'Column {col} not found in dataset')

    # Validate
    try:
        df_validated = validate_dataframe(df, config.get('validation', {}).get('required_columns', {}),
                                    config.get('validation', {}).get('numeric_columns', {}))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
        
    # Validated Rows removed
    df_validated_copy = df_validated.copy()
    rows_removed = len(df_original) - len(df_validated_copy)

    # Process
    try:
        df_processed = process_data(df_validated, config)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    # Report
    report = create_cleaning_report(df_validated_copy, df_processed)

    # Update
    storage.update(dataset_id, df_processed)

    # Log
    logger.info(
        f'Processed dataset: id={dataset_id} '
        f'validation_removed={rows_removed}, rows_before={len(df_validated_copy)}, rows_after={len(df_processed)}'
    )

    # Return
    return {'id': dataset_id,
            'validation_rows_removed':rows_removed,
            'cleaning_report':report
            }

@app.post("/movies/process", response_model=MovieProcessingReport)
def process_movies(config: ProcessConfig):
    # TODO 1: Retrieve data using storage.get().
    # Raise HTTPException with status 400 if empty.

    # TODO 2: Reuse MP2's configuration, validation, processing,
    # cleaning report, logging, and ValueError handling.

    # TODO 3: Save the processed DataFrame using storage.save().
    # Return validation_rows_removed and cleaning_report without a dataset ID.
    pass

@app.get("/movies/search", response_model=list[dict])
def query_movies(
    columns: list[str] = Query(default=["title"]),
    min_rating: float = Query(default=0, ge=0, le=10),
    limit: int = Query(default=100, ge=1)
):
    # TODO: Call storage.query_movies(columns, min_rating, limit).
    # Catch ValueError and raise HTTPException with status 400.
    # Return id plus the selected fields, or [] if there are no matches.
    # Log the selected columns and returned row count at INFO.
    pass

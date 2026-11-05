# src/data_output.py
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def save_data(df, filepath):
    """Save a DataFrame as a CSV file."""
    output_path = Path(filepath)

    output_path.parent.mkdir(parents=True, exist_ok=True) # create folder, checks if exists

    df.to_csv(filepath, index=False)
    logger.debug(f'Saved DF as CSV with {len(df)} rows at {filepath}')
    return filepath
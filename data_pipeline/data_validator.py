# src/data_validator.py
import logging
import pandas as pd


logger = logging.getLogger(__name__)


def validate_dataframe(df, required_columns, numeric_columns):
    """Validate the DataFrame and return valid data.

    required_columns: a list of column names that must exist.
    numeric_columns: a list of column names whose values should be numeric.
    """

    before = len(df) # rows before changes

    for col in required_columns:
        if col not in df.columns:
            logger.error(f'Column {col} not in dataframe')
            raise ValueError(f"Required column {col} does not exist")

    for col in numeric_columns:
        invalid_rows = []
        for i, value in df[col].items():
            if pd.notna(value):
                try:
                    float(value)
                except ValueError:
                    # Log a warning and record this row's index.
                    logger.warning(f"Row {i} contains invalid value: '{value}'")
                    invalid_rows.append(i)

        # Remove the invalid rows.
        if invalid_rows:
            logger.warning(f'Rows {invalid_rows} are invalid: removing them')
            df = df.drop(invalid_rows)

        # convert to a numeric data type
        df[col] = pd.to_numeric(df[col])
    logger.debug(f'Valid rows: {len(df)} | Removed Rows: {before - len(df)}')

    return df
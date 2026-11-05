# data_processor.py
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def remove_duplicates(df):
    """Remove duplicate rows."""
    rows = len(df) # number of rows before removal
    df = df.drop_duplicates() # removed dups
    rows_left = len(df) # rows after removed dups
    rows_removed = rows - rows_left # number rows removed
    logger.debug(f'Remove Duplicates: Removed {rows_removed} row(s) from dataframe.')
    return df


def handle_missing(df, axis="rows"):
    """Drop rows or columns containing missing values."""
    if axis == "rows":
        before = len(df)
        df = df.dropna()
        after = len(df)
        removed = before - after
        logger.debug(f'Remove Missing: Removed {removed} row(s) from dataframe.')
        return df

    elif axis == "columns":
        before = df.shape[1]
        df = df.dropna(axis=1)
        after = df.shape[1]
        removed = before - after
        logger.debug(f'Removed {removed} column(s) from dataframe.')
        return df

    else:
        logger.error(f'Axis {axis} is not supported.')
        raise ValueError('Axis must be either "rows" or "columns"')


def remove_outliers(df, columns, method, threshold):
    """Remove outliers from the specified numeric columns."""

    if method not in ['iqr', 'zscore']:
        logger.error(f'Method {method} is not supported.')
        raise ValueError(f'Method {method} not supported. Must be "iqr" or "zscore".')

    for col in columns:
        if col not in df.columns:
            logger.warning(f'Column {col} is not in the dataframe: skipping.')
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            logger.warning(f'Column {col} is not numeric. Skipping.')
            continue

        before = len(df)

        if method == 'iqr':
            q1 = df[col].quantile(.25)
            q3 = df[col].quantile(.75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

            df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]

            logger.debug(f'Method {method} initiated with threshold {threshold}. '
                         f'| Upper {upper_bound} | Lower {lower_bound} | '
                         f'{before - len(df)} row(s) removed.')

        else:
            z_score = abs(df[col] - df[col].mean()) / df[col].std()
            df = df[z_score <= threshold]

            logger.debug(f'Method {method} initiated with threshold {threshold}. '
                         f'{before - len(df)} row(s) removed.')
    return df



def process_data(df, config):
    """Apply the processing steps enabled in the configuration."""
    step = config['processing']

    if step.get('remove_duplicates'):
        df = remove_duplicates(df)

    missing = step.get('missing')
    if missing.get('enabled'):
        df = handle_missing(df, missing.get('axis', 'rows'))

    outliers = step.get('outliers')
    if outliers.get('enabled'):
         df = remove_outliers(df, outliers['columns'],
                             outliers['method'], outliers['threshold'])
    return df

def create_cleaning_report(df_before, df_after):
    """Return a dictionary summarizing the cleaning results."""
    rows_before = len(df_before)
    rows_after = len(df_after)
    rows_removed = rows_before - rows_after
    columns_before = df_before.shape[1]
    columns_after = df_after.shape[1]
    columns_removed = columns_before - columns_after

    return {
        'rows_before': rows_before,
        'rows_after': rows_after,
        'rows_removed': rows_removed,
        'columns_before': columns_before,
        'columns_after': columns_after,
        'columns_removed': columns_removed,
    }

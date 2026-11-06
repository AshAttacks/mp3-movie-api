import logging
import sqlite3

import pandas as pd

from .database import get_connection, initialize_database

logger = logging.getLogger(__name__)
MOVIE_COLUMNS = ["title", "release_year", "rating", "genre"]


class MovieStorage:
    def __init__(self, db_path="data/movies.db"):
        self.db_path = db_path
        initialize_database(self.db_path)

    def save(self, df):
        """Replace all movie rows in one transaction."""
        # TODO: Convert missing values to Python None for SQL NULL.
        clean = df.astype(object).where(pd.notna(df), None)
        rows = clean[MOVIE_COLUMNS].itertuples(index=False, name=None)
        # DELETE the old rows, then INSERT all rows from df.

        connection = get_connection(self.db_path)

        sql_statement_del = "DELETE FROM movies"
        sql_statement_insert = "INSERT INTO movies (title, release_year, rating, genre) VALUES (?, ?, ?, ?)"

        try:
            connection.execute(sql_statement_del)
            connection.executemany(sql_statement_insert, rows)
            connection.commit()
            logger.debug(f"Saved {len(df)} rows to database.")
        except sqlite3.Error:
            connection.rollback()
            raise
        finally:
            # Commit only after all inserts succeed; roll back on SQLite errors.
            # Close the connection in finally. Log the saved row count at DEBUG.
            connection.close()

    def get(self):
        """Return the four movie columns as a DataFrame, ordered by id."""
        # TODO: SELECT the four fields, fetch rows, and create the DataFrame.
        connection = get_connection(self.db_path)
        data = connection.execute(f"SELECT * FROM movies ORDER BY id DESC").fetchall()

        # Return a DataFrame with columns=MOVIE_COLUMNS,
        df = pd.DataFrame(data, columns=["id", "title", "release_year", "rating", "genre"])
        # so the column names are preserved even when the query returns no rows.
        return df

    def select_columns(self, columns, limit=5):
        """Return id plus the requested movie columns, ordered by id."""
        if not columns:
            logger.error("Select at least one column")
            raise ValueError("Select at least one column")

        for column in columns:
            if column not in MOVIE_COLUMNS:
                logger.error(f"Unsupported column: {column}")
                raise ValueError(f"Unsupported column: {column}")

        selected_columns = ", ".join(["id"] + columns)
        connection = get_connection(self.db_path)
        try:
            # TODO: SELECT selected_columns from movies, ordered by id.
            connection.execute('SELECT ? FROM movies ORDER BY id DESC LIMIT ?',
                               (selected_columns, limit)).fetchall()
            # Use a placeholder for limit; fetch the rows.
            # Return a list of dictionaries and log at DEBUG.
            list_dict = list(dict.fromkeys(selected_columns))
            logger.debug(f"Returned list of columns.") # REDO
            return list_dict
        finally:
            connection.close()

    def count_movies(self):
        """Return the number of stored movies using SQL COUNT(*)."""
        connection = get_connection(self.db_path)
        sql_statement = "SELECT COUNT(*) FROM movies"
        count = connection.execute(sql_statement).fetchone([0])
        return count

    def query_movies(self, columns, min_rating, limit):
        """Return selected fields from matching movies using SQL."""
        # TODO: validate columns as in select_columns().
        # SELECT id plus those columns and filter by minimum rating.
        # Sort by rating DESC then id ASC, and apply limit.
        # Return dictionaries and log the selected columns and row count at DEBUG.
        pass
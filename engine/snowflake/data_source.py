"""
engine/snowflake/data_source.py

Fetches structured data from Snowflake tables/views for assessment.
Returns a pandas DataFrame using the same interface as the CSV upload path
so the assessment engine works identically regardless of data source.
"""
from __future__ import annotations

import os
import pandas as pd


def list_tables(database: str | None = None, schema: str | None = None) -> list[dict]:
    """
    List available tables the service user can access.
    Searches all schemas in the database (excluding system schemas).
    """
    from engine.snowflake.connection import get_session
    session = get_session()

    db = database or os.environ.get("SNOWFLAKE_DATABASE", "DQ_ACCELERATOR")

    rows = session.sql(f"SHOW TABLES IN DATABASE {db}").collect()
    tables = []
    for r in rows:
        schema_name = r[3] if len(r) > 3 else ""
        table_name  = r[1] if len(r) > 1 else ""
        if schema_name and schema_name not in ("INFORMATION_SCHEMA",):
            # Get real row count
            try:
                count = session.sql(
                    f"SELECT COUNT(*) FROM {db}.{schema_name}.{table_name}"
                ).collect()[0][0]
            except Exception:
                count = 0
            tables.append({
                "database":  db,
                "schema":    schema_name,
                "name":      table_name,
                "type":      "TABLE",
                "row_count": count,
                "full_name": f"{db}.{schema_name}.{table_name}",
            })
    return sorted(tables, key=lambda x: (x["schema"], x["name"]))


def fetch_sample(
    full_table_name: str,
    limit: int = 5000,
) -> pd.DataFrame:
    """
    Fetch a sample of rows from a Snowflake table into a pandas DataFrame.

    Args:
        full_table_name: Fully qualified table name e.g. DB.SCHEMA.TABLE
        limit: Max rows to fetch (default 5000 — enough for assessment)

    Returns:
        pandas DataFrame with lowercase column names
    """
    from engine.snowflake.connection import get_session
    session = get_session()

    df = session.sql(
        f"SELECT * FROM {full_table_name} LIMIT {limit}"
    ).to_pandas()

    df.columns = [c.lower() for c in df.columns]
    return df


def get_table_preview(full_table_name: str, rows: int = 10) -> pd.DataFrame:
    """Fetch a small preview for display in the UI."""
    from engine.snowflake.connection import get_session
    session = get_session()

    df = session.sql(
        f"SELECT * FROM {full_table_name} LIMIT {rows}"
    ).to_pandas()
    df.columns = [c.lower() for c in df.columns]
    return df


def get_row_count(full_table_name: str) -> int:
    """Get exact row count for a table."""
    from engine.snowflake.connection import get_session
    session = get_session()
    result = session.sql(f"SELECT COUNT(*) FROM {full_table_name}").collect()
    return result[0][0] if result else 0

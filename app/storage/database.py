from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import get_settings
from app.storage.schema import SCHEMA_SQL
from app.utils import get_logger


logger = get_logger(__name__)


class DatabaseManager:
    def __init__(self, database_url: str | None = None) -> None:
        settings = get_settings()
        self.database_url = self._normalize_database_url(database_url or settings.database_url)
        self.engine: Engine = create_engine(self.database_url, future=True)

    def initialize_database(self) -> None:
        settings = get_settings()
        settings.processed_path.mkdir(parents=True, exist_ok=True)
        with self.engine.begin() as connection:
            for statement in SCHEMA_SQL:
                connection.execute(text(statement))
        logger.info("Database initialized at %s", self.database_url)

    @contextmanager
    def begin(self) -> Iterator:
        with self.engine.begin() as connection:
            yield connection

    def upsert_dataframe(self, table_name: str, frame: pd.DataFrame, pk_columns: list[str]) -> None:
        if frame.empty:
            logger.info("Skipping upsert for %s because dataframe is empty", table_name)
            return

        current = frame.copy()
        records = current.to_dict(orient="records")
        columns = list(current.columns)
        placeholders = ", ".join(f":{column}" for column in columns)
        update_columns = [column for column in columns if column not in pk_columns]
        update_clause = ", ".join(f"{column}=excluded.{column}" for column in update_columns)

        sql = f"""
        INSERT INTO {table_name} ({", ".join(columns)})
        VALUES ({placeholders})
        ON CONFLICT ({", ".join(pk_columns)}) DO UPDATE SET
        {update_clause};
        """

        with self.begin() as connection:
            connection.execute(text(sql), records)
        logger.info("Upserted %s rows into %s", len(records), table_name)

    def read_sql(self, query: str) -> pd.DataFrame:
        return pd.read_sql(query, self.engine)

    def write_export(self, frame: pd.DataFrame, filename: str) -> Path:
        settings = get_settings()
        settings.exports_path.mkdir(parents=True, exist_ok=True)
        export_path = settings.exports_path / filename
        frame.to_csv(export_path, index=False)
        logger.info("Exported dataset to %s", export_path)
        return export_path

    @staticmethod
    def _normalize_database_url(database_url: str) -> str:
        if database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql+psycopg://", 1)
        return database_url

from __future__ import annotations

from datetime import date, timedelta

from app.config import get_settings
from app.ingestion.cli_client import GarminCliClient
from app.ingestion.clients import BaseGarminClient, FileImportGarminClient, MockGarminClient
from app.ingestion.node_client import GarminNodeClient
from app.storage import DatabaseManager
from app.transformations.pipeline import normalize_ingested_data
from app.utils import get_logger


logger = get_logger(__name__)


PRIMARY_KEYS = {
    "daily_summary": ["summary_date"],
    "sleep": ["sleep_date"],
    "hrv": ["measurement_date"],
    "resting_hr": ["measurement_date"],
    "body_battery": ["measurement_date"],
    "training_readiness": ["measurement_date"],
    "training_status": ["measurement_date"],
    "activities": ["activity_id"],
    "activity_details": ["activity_id"],
    "weight_body_composition": ["measurement_date"],
}


class IngestionService:
    def __init__(self, db: DatabaseManager | None = None, client: BaseGarminClient | None = None) -> None:
        self.settings = get_settings()
        self.db = db or DatabaseManager()
        self.client = client or self._build_client()

    def _build_client(self) -> BaseGarminClient:
        source = self.settings.garmin_source.lower()
        if source == "mock":
            return MockGarminClient()
        if source == "node":
            return GarminNodeClient(self.settings.garmin_node_command)
        if source == "cli":
            return GarminCliClient(self.settings.garmin_cli_command)
        if source == "files":
            return FileImportGarminClient(self.settings.imports_path)
        logger.warning("Unknown GARMIN_SOURCE=%s. Falling back to mock.", source)
        return MockGarminClient()

    def ingest_range(self, start_date: date, end_date: date, save_raw: bool | None = None) -> dict[str, int]:
        save_raw = self.settings.save_raw_responses if save_raw is None else save_raw
        result = self.client.fetch(start_date=start_date, end_date=end_date, save_raw=save_raw)
        normalized = normalize_ingested_data(result.data, result.source, result.raw_payload_paths)

        counts: dict[str, int] = {}
        for table_name, frame in normalized.items():
            if table_name not in PRIMARY_KEYS:
                continue
            self.db.upsert_dataframe(table_name, frame, PRIMARY_KEYS[table_name])
            counts[table_name] = len(frame)
        return counts

    def ingest_last_days(self, days: int) -> dict[str, int]:
        end_date = date.today()
        start_date = end_date - timedelta(days=max(days - 1, 0))
        return self.ingest_range(start_date, end_date)

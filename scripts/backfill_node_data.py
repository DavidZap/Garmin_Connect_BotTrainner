from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analytics import AnalyticsService
from app.ingestion import IngestionService
from app.insights import InsightService
from app.storage import DatabaseManager
from app.utils import configure_logging, get_logger


configure_logging()
logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill all activity-based history available through the Node bridge.")
    parser.add_argument("--start-date", type=str, default=None, help="Optional explicit start date in YYYY-MM-DD format.")
    return parser.parse_args()


def detect_start_date(db: DatabaseManager) -> date | None:
    activities = db.read_sql("SELECT MIN(activity_date) AS min_date FROM activities")
    if activities.empty or activities.iloc[0]["min_date"] is None:
        return None
    return date.fromisoformat(str(activities.iloc[0]["min_date"]))


def main() -> None:
    args = parse_args()
    ingestion = IngestionService()
    ingestion.settings.garmin_source = "node"
    ingestion.client = ingestion._build_client()

    today = date.today()
    if args.start_date:
        start_date = date.fromisoformat(args.start_date)
    else:
        counts = ingestion.ingest_last_days(30)
        logger.info("Seed node sync counts: %s", counts)
        start_date = detect_start_date(ingestion.db)
        if start_date is None:
            raise RuntimeError("No se pudo inferir la fecha inicial desde las actividades disponibles.")

    counts = ingestion.ingest_range(start_date, today)
    logger.info("Backfill node sync counts: %s", counts)

    analytics = AnalyticsService(ingestion.db)
    derived = analytics.persist_derived_metrics()
    insights = InsightService(ingestion.db, analytics).persist_insights()
    logger.info("Backfill completed: %s derived rows, %s insights", len(derived), len(insights))


if __name__ == "__main__":
    main()

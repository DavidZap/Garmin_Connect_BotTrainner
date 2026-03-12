from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analytics import AnalyticsService
from app.ingestion import IngestionService
from app.insights import InsightService
from app.utils import configure_logging, get_logger


configure_logging()
logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import real Garmin-compatible files from data/imports.")
    parser.add_argument("--days", type=int, default=3650, help="Number of days to scan backward when filtering imported files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    service = IngestionService()
    service.settings.garmin_source = "files"
    service.client = service._build_client()

    counts = service.ingest_last_days(args.days)
    logger.info("Imported file counts: %s", counts)

    analytics = AnalyticsService(service.db)
    derived = analytics.persist_derived_metrics()
    insights = InsightService(service.db, analytics).persist_insights()
    logger.info("Import completed: %s derived rows, %s insights", len(derived), len(insights))


if __name__ == "__main__":
    main()

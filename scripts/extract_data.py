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
    parser = argparse.ArgumentParser(description="Extract Garmin data and persist it.")
    parser.add_argument("--days", type=int, default=14, help="Number of days to ingest.")
    parser.add_argument("--use-mock", action="store_true", help="Force mock data source.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    service = IngestionService()
    if args.use_mock:
        service.settings.garmin_source = "mock"
        service.client = service._build_client()

    counts = service.ingest_last_days(args.days)
    logger.info("Ingestion counts: %s", counts)

    analytics = AnalyticsService(service.db)
    analytics.persist_derived_metrics()
    InsightService(service.db, analytics).persist_insights()
    logger.info("Extraction pipeline completed successfully.")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
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
    parser = argparse.ArgumentParser(description="Load historical Garmin data.")
    parser.add_argument("--days", type=int, default=180, help="Days of historical data to ingest.")
    parser.add_argument("--use-mock", action="store_true", help="Force mock generation.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ingestion = IngestionService()
    if args.use_mock:
        ingestion.settings.garmin_source = "mock"
        ingestion.client = ingestion._build_client()

    end_date = date.today()
    start_date = end_date - timedelta(days=max(args.days - 1, 0))
    counts = ingestion.ingest_range(start_date, end_date)
    logger.info("Historical load counts: %s", counts)

    analytics = AnalyticsService(ingestion.db)
    analytics.persist_derived_metrics()
    InsightService(ingestion.db, analytics).persist_insights()
    logger.info("Historical load completed.")


if __name__ == "__main__":
    main()

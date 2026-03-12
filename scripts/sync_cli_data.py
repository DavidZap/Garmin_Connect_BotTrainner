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
    parser = argparse.ArgumentParser(description="Sync Garmin data using the garmin-connect CLI.")
    parser.add_argument("--days", type=int, default=30, help="Recent days to sync via CLI.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ingestion = IngestionService()
    ingestion.settings.garmin_source = "cli"
    ingestion.client = ingestion._build_client()

    counts = ingestion.ingest_last_days(args.days)
    logger.info("CLI sync counts: %s", counts)

    analytics = AnalyticsService(ingestion.db)
    derived = analytics.persist_derived_metrics()
    insights = InsightService(ingestion.db, analytics).persist_insights()
    logger.info("CLI sync completed: %s derived rows, %s insights", len(derived), len(insights))


if __name__ == "__main__":
    main()

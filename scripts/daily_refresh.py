from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analytics import AnalyticsService
from app.ingestion import IngestionService
from app.insights import InsightService, NarrativeInsightService
from app.utils import configure_logging, get_logger


configure_logging()
logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the daily Garmin refresh pipeline.")
    parser.add_argument("--days", type=int, default=7, help="Recent days to refresh from the active Garmin source.")
    parser.add_argument("--source", type=str, default="node", help="Data source to use: node, files or mock.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ingestion = IngestionService()
    ingestion.settings.garmin_source = args.source
    ingestion.client = ingestion._build_client()

    counts = ingestion.ingest_last_days(args.days)
    logger.info("Daily refresh ingestion counts: %s", counts)

    analytics = AnalyticsService(ingestion.db)
    derived = analytics.persist_derived_metrics()

    insights_service = InsightService(ingestion.db, analytics)
    insights = insights_service.persist_insights()

    report_path = None
    try:
        report = NarrativeInsightService(ingestion.db).build_weekly_markdown_report()
        exports_path = ingestion.settings.exports_path
        exports_path.mkdir(parents=True, exist_ok=True)
        report_path = exports_path / "weekly_report_latest.md"
        report_path.write_text(report, encoding="utf-8")
    except Exception as exc:
        logger.warning("Weekly report export failed during daily refresh: %s", exc)

    logger.info(
        "Daily refresh completed: %s derived rows, %s insights, report=%s",
        len(derived),
        len(insights),
        report_path or "not_generated",
    )


if __name__ == "__main__":
    main()

from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analytics import AnalyticsService
from app.insights import InsightService
from app.utils import configure_logging, get_logger


configure_logging()
logger = get_logger(__name__)


def main() -> None:
    analytics = AnalyticsService()
    derived = analytics.persist_derived_metrics()
    insights = InsightService(analytics=analytics).persist_insights()
    logger.info("Recalculated %s derived rows and %s insights", len(derived), len(insights))


if __name__ == "__main__":
    main()

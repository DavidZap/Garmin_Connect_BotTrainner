from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analytics import AnalyticsService
from app.utils import configure_logging, get_logger


configure_logging()
logger = get_logger(__name__)


def main() -> None:
    derived = AnalyticsService().persist_derived_metrics()
    logger.info("Derived metrics recalculated: %s rows", len(derived))


if __name__ == "__main__":
    main()

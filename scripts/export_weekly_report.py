from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import get_settings
from app.insights import NarrativeInsightService
from app.utils import configure_logging, get_logger


configure_logging()
logger = get_logger(__name__)


def main() -> None:
    settings = get_settings()
    settings.exports_path.mkdir(parents=True, exist_ok=True)
    report = NarrativeInsightService().build_weekly_markdown_report()
    output_path = settings.exports_path / f"weekly_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    output_path.write_text(report, encoding="utf-8")
    logger.info("Weekly report exported to %s", output_path)


if __name__ == "__main__":
    main()

from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import get_settings
from app.storage import DatabaseManager
from app.utils import configure_logging, get_logger


configure_logging()
logger = get_logger(__name__)


def ensure_directories() -> None:
    settings = get_settings()
    directories = [
        settings.data_path,
        settings.imports_path,
        settings.raw_path,
        settings.processed_path,
        settings.exports_path,
        settings.root_dir / "docs",
        settings.root_dir / "tests",
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info("Ensured directory: %s", directory)


def main() -> None:
    ensure_directories()
    DatabaseManager().initialize_database()
    logger.info("Project initialized successfully.")


if __name__ == "__main__":
    main()

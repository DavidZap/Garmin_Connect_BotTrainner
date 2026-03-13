from __future__ import annotations

import sys
from pathlib import Path

import uvicorn

from app.config import get_settings


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def main() -> None:
    settings = get_settings()
    uvicorn.run("app.api.main:app", host=settings.app_host, port=settings.app_port, reload=False)


if __name__ == "__main__":
    main()

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    root_dir = Path(__file__).resolve().parents[1]
    dashboard_path = root_dir / "app" / "dashboard" / "streamlit_app.py"
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(dashboard_path)], check=True)


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.storage import DatabaseManager
from app.utils import configure_logging, get_logger


configure_logging()
logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add or update a manual daily check-in.")
    parser.add_argument("--date", dest="checkin_date", default=date.today().isoformat(), help="Check-in date in YYYY-MM-DD.")
    parser.add_argument("--energy", type=int, default=None, help="Perceived energy 1-5.")
    parser.add_argument("--stress", type=int, default=None, help="Work stress 1-5.")
    parser.add_argument("--soreness", type=int, default=None, help="Muscle soreness 1-5.")
    parser.add_argument("--hydration", type=int, default=None, help="Hydration quality 1-5.")
    parser.add_argument("--nutrition", type=int, default=None, help="Nutrition quality 1-5.")
    parser.add_argument("--mood", type=int, default=None, help="Mood 1-5.")
    parser.add_argument("--strength-load", type=int, default=None, help="Strength training load 1-5.")
    parser.add_argument("--cycle-phase", default=None, help="Optional menstrual cycle phase.")
    parser.add_argument("--notes", default=None, help="Free-form notes.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db = DatabaseManager()
    frame = pd.DataFrame(
        [
            {
                "checkin_date": args.checkin_date,
                "perceived_energy": args.energy,
                "work_stress": args.stress,
                "muscle_soreness": args.soreness,
                "hydration": args.hydration,
                "nutrition_quality": args.nutrition,
                "mood": args.mood,
                "strength_training_load": args.strength_load,
                "menstrual_cycle_phase": args.cycle_phase,
                "notes": args.notes,
                "source": "manual_cli",
            }
        ]
    )
    db.upsert_dataframe("manual_checkins", frame, ["checkin_date"])
    logger.info("Manual check-in upserted for %s", args.checkin_date)


if __name__ == "__main__":
    main()

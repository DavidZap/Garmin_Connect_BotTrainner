from __future__ import annotations

import pandas as pd

from app.storage import DatabaseManager
from app.transformations import build_daily_analytics_frame
from app.utils import get_logger


logger = get_logger(__name__)

DEFAULT_DAILY_COLUMNS = {
    "duration_hours": 0.0,
    "overnight_avg": 0.0,
    "resting_hr_bpm": 0.0,
    "readiness_score": 0.0,
    "body_battery_avg": 0.0,
    "total_training_load": 0.0,
    "activity_count": 0.0,
    "total_duration_minutes": 0.0,
    "weight_kg": 0.0,
    "body_fat_pct": 0.0,
    "muscle_mass_kg": 0.0,
    "body_water_pct": 0.0,
    "perceived_energy": 0.0,
    "work_stress": 0.0,
    "muscle_soreness": 0.0,
    "hydration": 0.0,
    "nutrition_quality": 0.0,
    "mood": 0.0,
    "strength_training_load": 0.0,
}


class AnalyticsService:
    def __init__(self, db: DatabaseManager | None = None) -> None:
        self.db = db or DatabaseManager()

    def load_base_frames(self) -> dict[str, pd.DataFrame]:
        tables = [
            "daily_summary",
            "sleep",
            "hrv",
            "resting_hr",
            "body_battery",
            "training_readiness",
            "training_status",
            "activities",
            "weight_body_composition",
            "manual_checkins",
        ]
        return {table: self.db.read_sql(f"SELECT * FROM {table}") for table in tables}

    def calculate_derived_metrics(self) -> pd.DataFrame:
        frames = self.load_base_frames()
        if frames["daily_summary"].empty:
            logger.warning("No daily_summary data available for metric calculation.")
            return pd.DataFrame()

        daily = build_daily_analytics_frame(frames).sort_values("metric_date").reset_index(drop=True)
        daily = self._ensure_default_columns(daily)

        daily["sleep_hours_7d"] = daily["duration_hours"].rolling(7, min_periods=1).mean()
        daily["sleep_hours_28d"] = daily["duration_hours"].rolling(28, min_periods=1).mean()
        daily["hrv_7d"] = daily["overnight_avg"].rolling(7, min_periods=1).mean()
        daily["hrv_28d"] = daily["overnight_avg"].rolling(28, min_periods=1).mean()
        daily["resting_hr_7d"] = daily["resting_hr_bpm"].rolling(7, min_periods=1).mean()
        daily["resting_hr_28d"] = daily["resting_hr_bpm"].rolling(28, min_periods=1).mean()
        daily["training_load_7d"] = daily["total_training_load"].rolling(7, min_periods=1).sum()
        daily["training_load_28d"] = daily["total_training_load"].rolling(28, min_periods=1).mean()
        daily["acute_chronic_ratio"] = daily["training_load_7d"] / daily["training_load_28d"].replace(0, pd.NA)
        daily["sleep_variation_day"] = daily["duration_hours"].diff().fillna(0)
        daily["sleep_variation_week"] = daily["duration_hours"] - daily["sleep_hours_7d"]
        daily["hrv_rhr_ratio"] = daily["overnight_avg"] / daily["resting_hr_bpm"].replace(0, pd.NA)
        daily["load_readiness_ratio"] = daily["total_training_load"] / daily["readiness_score"].replace(0, pd.NA)
        daily["sleep_consistency_score"] = 100 - (daily["duration_hours"].rolling(7, min_periods=2).std().fillna(0) * 12).clip(lower=0, upper=100)

        daily["fatigue_flag"] = (
            (
                (daily["overnight_avg"] < daily["hrv_7d"] * 0.92)
                & (daily["resting_hr_bpm"] > daily["resting_hr_7d"] * 1.05)
            )
            | (daily["readiness_score"] < 40)
            | (daily["acute_chronic_ratio"] > 1.35)
        ).astype(int)

        fatigue_streaks: list[int] = []
        recovery_streaks: list[int] = []
        fatigue_run = 0
        recovery_run = 0
        for _, row in daily.iterrows():
            fatigue_run = fatigue_run + 1 if row["fatigue_flag"] == 1 else 0
            good_recovery = (
                row["duration_hours"] >= row["sleep_hours_7d"]
                and row["overnight_avg"] >= row["hrv_7d"]
                and row["readiness_score"] >= 65
            )
            recovery_run = recovery_run + 1 if good_recovery else 0
            fatigue_streaks.append(fatigue_run)
            recovery_streaks.append(recovery_run)

        derived = pd.DataFrame(
            {
                "metric_date": daily["metric_date"].dt.strftime("%Y-%m-%d"),
                "sleep_hours_7d": daily["sleep_hours_7d"].round(2),
                "sleep_hours_28d": daily["sleep_hours_28d"].round(2),
                "hrv_7d": daily["hrv_7d"].round(2),
                "hrv_28d": daily["hrv_28d"].round(2),
                "resting_hr_7d": daily["resting_hr_7d"].round(2),
                "resting_hr_28d": daily["resting_hr_28d"].round(2),
                "training_load_7d": daily["training_load_7d"].round(2),
                "training_load_28d": daily["training_load_28d"].round(2),
                "acute_chronic_ratio": daily["acute_chronic_ratio"].fillna(0).round(2),
                "sleep_variation_day": daily["sleep_variation_day"].round(2),
                "sleep_variation_week": daily["sleep_variation_week"].round(2),
                "hrv_rhr_ratio": daily["hrv_rhr_ratio"].fillna(0).round(2),
                "load_readiness_ratio": daily["load_readiness_ratio"].fillna(0).round(2),
                "sleep_consistency_score": daily["sleep_consistency_score"].round(2),
                "fatigue_flag": daily["fatigue_flag"].astype(int),
                "fatigue_streak": fatigue_streaks,
                "recovery_streak": recovery_streaks,
            }
        )
        return derived

    def persist_derived_metrics(self) -> pd.DataFrame:
        derived = self.calculate_derived_metrics()
        if not derived.empty:
            self.db.upsert_dataframe("derived_metrics", derived, ["metric_date"])
        return derived

    def build_dashboard_dataset(self) -> pd.DataFrame:
        frames = self.load_base_frames()
        if frames["daily_summary"].empty:
            return pd.DataFrame()
        daily = self._ensure_default_columns(build_daily_analytics_frame(frames))
        derived = self.db.read_sql("SELECT * FROM derived_metrics")
        if not derived.empty:
            derived["metric_date"] = pd.to_datetime(derived["metric_date"])
            daily = daily.merge(derived, on="metric_date", how="left")
        return daily.sort_values("metric_date")

    @staticmethod
    def _ensure_default_columns(frame: pd.DataFrame) -> pd.DataFrame:
        current = frame.copy()
        for column, default_value in DEFAULT_DAILY_COLUMNS.items():
            if column not in current.columns:
                current[column] = default_value
            else:
                current[column] = current[column].fillna(default_value)
        return current

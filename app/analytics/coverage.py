from __future__ import annotations

import pandas as pd

from app.storage import DatabaseManager


DATASET_CONFIG = {
    "daily_summary": {"date_column": "summary_date", "critical_columns": ["steps"]},
    "sleep": {"date_column": "sleep_date", "critical_columns": ["duration_hours", "sleep_score"]},
    "hrv": {"date_column": "measurement_date", "critical_columns": ["overnight_avg"]},
    "resting_hr": {"date_column": "measurement_date", "critical_columns": ["resting_hr_bpm"]},
    "body_battery": {"date_column": "measurement_date", "critical_columns": ["body_battery_avg"]},
    "training_readiness": {"date_column": "measurement_date", "critical_columns": ["readiness_score"]},
    "training_status": {"date_column": "measurement_date", "critical_columns": ["training_status"]},
    "activities": {"date_column": "activity_date", "critical_columns": ["activity_id", "training_load"]},
    "weight_body_composition": {"date_column": "measurement_date", "critical_columns": ["weight_kg"]},
    "manual_checkins": {"date_column": "checkin_date", "critical_columns": ["perceived_energy", "work_stress", "muscle_soreness"]},
}


class CoverageAnalyticsService:
    def __init__(self, db: DatabaseManager | None = None) -> None:
        self.db = db or DatabaseManager()

    def build_coverage_report(self) -> pd.DataFrame:
        report_rows: list[dict[str, object]] = []
        for table_name, config in DATASET_CONFIG.items():
            frame = self.db.read_sql(f"SELECT * FROM {table_name}")
            date_column = config["date_column"]
            critical_columns = config["critical_columns"]

            total_rows = len(frame)
            date_range_days = 0
            first_date = None
            last_date = None
            populated_days = 0
            coverage_pct = 0.0

            if not frame.empty and date_column in frame.columns:
                frame[date_column] = pd.to_datetime(frame[date_column], errors="coerce")
                frame = frame.dropna(subset=[date_column])
                if not frame.empty:
                    first_date = frame[date_column].min().date()
                    last_date = frame[date_column].max().date()
                    date_range_days = (last_date - first_date).days + 1
                    populated_days = frame[date_column].dt.date.nunique()
                    coverage_pct = round((populated_days / date_range_days) * 100, 1) if date_range_days else 0.0

            critical_available = 0
            critical_total = len(critical_columns)
            available_columns = ", ".join([column for column in critical_columns if column in frame.columns]) if not frame.empty else ""
            missing_columns = [column for column in critical_columns if frame.empty or column not in frame.columns]
            for column in critical_columns:
                if column in frame.columns and frame[column].notna().any():
                    critical_available += 1

            status = self._status_label(critical_available, critical_total, total_rows)
            report_rows.append(
                {
                    "dataset": table_name,
                    "status": status,
                    "total_rows": total_rows,
                    "first_date": first_date,
                    "last_date": last_date,
                    "date_range_days": date_range_days,
                    "populated_days": populated_days,
                    "coverage_pct": coverage_pct,
                    "critical_available": critical_available,
                    "critical_total": critical_total,
                    "available_columns": available_columns,
                    "missing_columns": ", ".join(missing_columns),
                }
            )

        return pd.DataFrame(report_rows).sort_values(["status", "coverage_pct"], ascending=[True, False])

    def build_availability_summary(self) -> str:
        report = self.build_coverage_report()
        if report.empty:
            return "No hay datasets disponibles."

        healthy = report[report["status"] == "ok"]["dataset"].tolist()
        partial = report[report["status"] == "partial"]["dataset"].tolist()
        missing = report[report["status"] == "missing"]["dataset"].tolist()

        return (
            f"Datasets utilizables: {', '.join(healthy) if healthy else 'ninguno'}. "
            f"Parciales: {', '.join(partial) if partial else 'ninguno'}. "
            f"Ausentes: {', '.join(missing) if missing else 'ninguno'}."
        )

    @staticmethod
    def _status_label(critical_available: int, critical_total: int, total_rows: int) -> str:
        if total_rows == 0 or critical_available == 0:
            return "missing"
        if critical_available < critical_total:
            return "partial"
        return "ok"

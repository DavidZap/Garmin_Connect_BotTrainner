from __future__ import annotations

import pandas as pd

from app.analytics import CoverageAnalyticsService
from app.analytics.metrics import AnalyticsService
from app.storage import DatabaseManager


class PerformanceAnalyticsService:
    def __init__(self, db: DatabaseManager | None = None, analytics: AnalyticsService | None = None) -> None:
        self.db = db or DatabaseManager()
        self.analytics = analytics or AnalyticsService(self.db)
        self.coverage = CoverageAnalyticsService(self.db)

    def build_day_rankings(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        dataset = self.analytics.build_dashboard_dataset()
        if dataset.empty:
            return pd.DataFrame(), pd.DataFrame()

        current = dataset.copy()
        current["metric_date"] = pd.to_datetime(current["metric_date"])
        current["recovery_score_local"] = (
            (current["duration_hours"] - current["duration_hours"].rolling(7, min_periods=1).mean()).fillna(0) * 8
            + (current["overnight_avg"] - current["overnight_avg"].rolling(7, min_periods=1).mean()).fillna(0) * 1.5
            - (current["resting_hr_bpm"] - current["resting_hr_bpm"].rolling(7, min_periods=1).mean()).fillna(0) * 4
            + (current["body_battery_avg"] - current["body_battery_avg"].rolling(7, min_periods=1).mean()).fillna(0) * 0.5
        )
        current["fatigue_score_local"] = (
            (current["resting_hr_bpm"] - current["resting_hr_bpm"].rolling(7, min_periods=1).mean()).fillna(0) * 4
            - (current["overnight_avg"] - current["overnight_avg"].rolling(7, min_periods=1).mean()).fillna(0) * 1.5
            + current["acute_chronic_ratio"].fillna(0) * 10
            - (current["duration_hours"] - current["duration_hours"].rolling(7, min_periods=1).mean()).fillna(0) * 5
        )

        best = (
            current.sort_values(["recovery_score_local", "duration_hours", "overnight_avg"], ascending=[False, False, False])
            .head(5)[["metric_date", "duration_hours", "overnight_avg", "resting_hr_bpm", "body_battery_avg", "total_training_load", "recovery_score_local"]]
            .copy()
        )
        worst = (
            current.sort_values(["fatigue_score_local", "duration_hours", "overnight_avg"], ascending=[False, True, True])
            .head(5)[["metric_date", "duration_hours", "overnight_avg", "resting_hr_bpm", "body_battery_avg", "total_training_load", "fatigue_score_local"]]
            .copy()
        )
        return best, worst

    def build_weekly_comparison(self) -> pd.DataFrame:
        dataset = self.analytics.build_dashboard_dataset()
        if dataset.empty:
            return pd.DataFrame()

        current = dataset.sort_values("metric_date").copy()
        current["metric_date"] = pd.to_datetime(current["metric_date"])
        recent = current.tail(7)
        previous = current.tail(14).head(7)
        if previous.empty:
            previous = recent.copy()

        rows = [
            self._compare_metric("Sueno", recent["duration_hours"], previous["duration_hours"], "h"),
            self._compare_metric("HRV", recent["overnight_avg"], previous["overnight_avg"], ""),
            self._compare_metric("Resting HR", recent["resting_hr_bpm"], previous["resting_hr_bpm"], "bpm"),
            self._compare_metric("Body Battery", recent["body_battery_avg"], previous["body_battery_avg"], ""),
            self._compare_metric("Carga total", recent["total_training_load"], previous["total_training_load"], "", aggregation="sum"),
            self._compare_metric("Duracion total actividades", recent["total_duration_minutes"], previous["total_duration_minutes"], "min", aggregation="sum"),
        ]
        return pd.DataFrame(rows)

    def build_fatigue_alerts(self) -> pd.DataFrame:
        dataset = self.analytics.build_dashboard_dataset()
        if dataset.empty:
            return pd.DataFrame()

        current = dataset.sort_values("metric_date").copy()
        alerts: list[dict[str, object]] = []
        for _, row in current.iterrows():
            conditions = []
            if row.get("overnight_avg", 0) < row.get("hrv_7d", 0) * 0.92:
                conditions.append("HRV por debajo de base 7d")
            if row.get("resting_hr_bpm", 0) > row.get("resting_hr_7d", 0) * 1.05:
                conditions.append("Resting HR por encima de base 7d")
            if row.get("acute_chronic_ratio", 0) > 1.2:
                conditions.append("Carga subiendo rapido")
            if row.get("duration_hours", 0) < 6.5:
                conditions.append("Sueno corto")
            if row.get("perceived_energy", 0) and row.get("perceived_energy", 0) <= 2:
                conditions.append("Energia percibida baja")
            if row.get("work_stress", 0) and row.get("work_stress", 0) >= 4:
                conditions.append("Estres laboral alto")
            if row.get("muscle_soreness", 0) and row.get("muscle_soreness", 0) >= 4:
                conditions.append("Dolor muscular alto")

            if len(conditions) >= 2:
                alerts.append(
                    {
                        "metric_date": pd.to_datetime(row["metric_date"]).strftime("%Y-%m-%d"),
                        "severity": "high" if len(conditions) >= 3 else "medium",
                        "signals": ", ".join(conditions),
                    }
                )
        return pd.DataFrame(alerts)

    @staticmethod
    def _compare_metric(
        label: str,
        recent_series: pd.Series,
        previous_series: pd.Series,
        unit: str,
        aggregation: str = "mean",
    ) -> dict[str, object]:
        if aggregation == "sum":
            recent_value = float(recent_series.sum())
            previous_value = float(previous_series.sum())
        else:
            recent_value = float(recent_series.mean())
            previous_value = float(previous_series.mean())
        delta = recent_value - previous_value
        return {
            "metric": label,
            "recent": round(recent_value, 2),
            "previous": round(previous_value, 2),
            "delta": round(delta, 2),
            "direction": "sube" if delta > 0 else "baja" if delta < 0 else "estable",
            "unit": unit,
        }

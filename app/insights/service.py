from __future__ import annotations

import json
import uuid

import pandas as pd

from app.analytics import AnalyticsService
from app.insights.rules import INSIGHT_RULES
from app.storage import DatabaseManager
from app.utils import get_logger


logger = get_logger(__name__)


class InsightService:
    def __init__(self, db: DatabaseManager | None = None, analytics: AnalyticsService | None = None) -> None:
        self.db = db or DatabaseManager()
        self.analytics = analytics or AnalyticsService(self.db)

    def generate_insights(self) -> pd.DataFrame:
        dataset = self.analytics.build_dashboard_dataset()
        if dataset.empty:
            logger.warning("No data available to generate insights.")
            return pd.DataFrame()

        dataset = dataset.sort_values("metric_date").copy()
        insights: list[dict[str, str]] = []

        for _, row in dataset.iterrows():
            if row.get("overnight_avg", 0) and (
                row.get("overnight_avg", 0) < row.get("hrv_7d", 0) * 0.92
                or row.get("overnight_avg", 0) < row.get("hrv_28d", 0) * 0.88
            ):
                insights.append(
                    self._build_insight(
                        row,
                        "hrv_drop_vs_baseline",
                        "high" if row.get("overnight_avg", 0) < row.get("hrv_28d", 0) * 0.88 else "medium",
                        INSIGHT_RULES[0].explanation_template.format(
                            overnight_avg=row.get("overnight_avg", 0),
                            hrv_7d=row.get("hrv_7d", 0),
                            hrv_28d=row.get("hrv_28d", 0),
                        ),
                        INSIGHT_RULES[0].recommendation,
                    )
                )

            if row.get("resting_hr_bpm", 0) > row.get("resting_hr_7d", 0) * 1.05:
                insights.append(
                    self._build_insight(
                        row,
                        "resting_hr_increase_vs_baseline",
                        "medium",
                        INSIGHT_RULES[1].explanation_template.format(
                            resting_hr_bpm=row.get("resting_hr_bpm", 0),
                            resting_hr_7d=row.get("resting_hr_7d", 0),
                        ),
                        INSIGHT_RULES[1].recommendation,
                    )
                )

            if row.get("duration_hours", 0) < 6.5 and row.get("total_training_load", 0) > max(row.get("training_load_7d", 0) / 7, 60):
                insights.append(
                    self._build_insight(
                        row,
                        "insufficient_sleep_before_high_load",
                        "high" if row.get("duration_hours", 0) < 5.8 else "medium",
                        INSIGHT_RULES[2].explanation_template.format(
                            duration_hours=row.get("duration_hours", 0),
                            total_training_load=row.get("total_training_load", 0),
                        ),
                        INSIGHT_RULES[2].recommendation,
                    )
                )

            if row.get("readiness_score", 0) < 45 and row.get("fatigue_streak", 0) >= 3:
                insights.append(
                    self._build_insight(
                        row,
                        "persistent_low_readiness",
                        "high",
                        INSIGHT_RULES[3].explanation_template.format(readiness_score=row.get("readiness_score", 0)),
                        INSIGHT_RULES[3].recommendation,
                    )
                )

            if row.get("fatigue_streak", 0) >= 3:
                insights.append(
                    self._build_insight(
                        row,
                        "multi_day_fatigue_signals",
                        "high",
                        INSIGHT_RULES[4].explanation_template.format(fatigue_streak=row.get("fatigue_streak", 0)),
                        INSIGHT_RULES[4].recommendation,
                    )
                )

            balanced_week = (
                row.get("readiness_score", 0) >= 60
                and 0.8 <= row.get("acute_chronic_ratio", 0) <= 1.2
                and row.get("duration_hours", 0) >= row.get("sleep_hours_7d", 0)
            )
            if balanced_week:
                insights.append(
                    self._build_insight(
                        row,
                        "balanced_load_recovery_week",
                        "positive",
                        INSIGHT_RULES[5].explanation_template,
                        INSIGHT_RULES[5].recommendation,
                    )
                )

        insight_frame = pd.DataFrame(insights)
        return insight_frame.drop_duplicates(subset=["insight_date", "insight_name", "severity"]) if not insight_frame.empty else insight_frame

    def persist_insights(self) -> pd.DataFrame:
        insight_frame = self.generate_insights()
        if not insight_frame.empty:
            self.db.upsert_dataframe("insights_history", insight_frame, ["insight_id"])
        return insight_frame

    def build_daily_summary_text(self) -> str:
        dataset = self.analytics.build_dashboard_dataset()
        if dataset.empty:
            return "No hay datos suficientes para generar un resumen diario."
        latest = dataset.sort_values("metric_date").iloc[-1]
        return (
            f"Resumen diario {latest['metric_date'].date()}: "
            f"sueno {latest.get('duration_hours', 0):.1f}h, HRV {latest.get('overnight_avg', 0):.1f}, "
            f"RHR {latest.get('resting_hr_bpm', 0):.1f}, readiness {latest.get('readiness_score', 0):.0f}, "
            f"carga {latest.get('total_training_load', 0):.0f}."
        )

    def build_weekly_summary_text(self) -> str:
        dataset = self.analytics.build_dashboard_dataset()
        if dataset.empty:
            return "No hay datos suficientes para generar un resumen semanal."
        recent = dataset.sort_values("metric_date").tail(7)
        previous = dataset.sort_values("metric_date").tail(14).head(7)
        if previous.empty:
            previous = recent
        return (
            f"Semana reciente: sueno promedio {recent['duration_hours'].mean():.1f}h vs {previous['duration_hours'].mean():.1f}h; "
            f"HRV {recent['overnight_avg'].mean():.1f} vs {previous['overnight_avg'].mean():.1f}; "
            f"readiness {recent['readiness_score'].mean():.1f} vs {previous['readiness_score'].mean():.1f}; "
            f"carga total {recent['total_training_load'].sum():.0f}."
        )

    def _build_insight(
        self,
        row: pd.Series,
        name: str,
        severity: str,
        explanation: str,
        recommendation: str,
    ) -> dict[str, str]:
        metric_date = pd.to_datetime(row["metric_date"]).strftime("%Y-%m-%d")
        payload = {
            "name": name,
            "logic_inputs": {k: self._safe_value(v) for k, v in row.to_dict().items()},
            "rule": next((rule.logic for rule in INSIGHT_RULES if rule.name == name), ""),
        }
        return {
            "insight_id": str(uuid.uuid4()),
            "insight_date": metric_date,
            "insight_name": name,
            "severity": severity,
            "explanation": explanation,
            "recommendation": recommendation,
            "metric_date": metric_date,
            "payload_json": json.dumps(payload, ensure_ascii=True),
        }

    @staticmethod
    def _safe_value(value: object) -> object:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return value


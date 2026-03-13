from __future__ import annotations

import pandas as pd

from app.analytics import PerformanceAnalyticsService
from app.storage import DatabaseManager


class NarrativeInsightService:
    def __init__(self, db: DatabaseManager | None = None, performance: PerformanceAnalyticsService | None = None) -> None:
        self.db = db or DatabaseManager()
        self.performance = performance or PerformanceAnalyticsService(self.db)

    def build_weekly_narrative(self) -> str:
        comparison = self.performance.build_weekly_comparison()
        if comparison.empty:
            return "No hay datos suficientes para construir una narrativa semanal."

        lookup = {row["metric"]: row for _, row in comparison.iterrows()}
        sleep = lookup.get("Sueno")
        hrv = lookup.get("HRV")
        rhr = lookup.get("Resting HR")
        load = lookup.get("Carga total")

        messages: list[str] = []
        if sleep is not None:
            if sleep["delta"] >= 0.3:
                messages.append("Dormiste mas que la semana previa, lo que favorece la recuperacion.")
            elif sleep["delta"] <= -0.3:
                messages.append("Dormiste menos que la semana previa, una senal a vigilar si coincide con carga alta.")

        if hrv is not None and rhr is not None:
            if hrv["delta"] > 0 and rhr["delta"] < 0:
                messages.append("La combinacion de HRV al alza y resting HR a la baja sugiere mejor tono de recuperacion.")
            elif hrv["delta"] < 0 and rhr["delta"] > 0:
                messages.append("La HRV cayo mientras el resting HR subio, patron compatible con mayor estres fisiologico.")

        if load is not None:
            if load["delta"] > 50:
                messages.append("La carga total subio de forma visible frente a la semana previa.")
            elif load["delta"] < -50:
                messages.append("La carga total fue menor que la semana previa, lo que puede reflejar descarga o menor volumen.")

        if not messages:
            messages.append("La semana luce relativamente estable frente a la anterior, sin cambios fuertes en las senales principales.")

        return " ".join(messages)

    def build_best_day_narrative(self) -> str:
        best_days, _ = self.performance.build_day_rankings()
        if best_days.empty:
            return "No hay datos suficientes para describir tus mejores dias."

        top = best_days.iloc[0]
        return (
            f"Tu mejor dia reciente fue {pd.to_datetime(top['metric_date']).date()}: "
            f"combino {top['duration_hours']:.1f}h de sueno, HRV {top['overnight_avg']:.1f}, "
            f"resting HR {top['resting_hr_bpm']:.1f} y body battery {top['body_battery_avg']:.1f}. "
            "Este perfil sugiere buena recuperacion basal relativa frente a tus dias cercanos."
        )

    def build_worst_day_narrative(self) -> str:
        _, worst_days = self.performance.build_day_rankings()
        if worst_days.empty:
            return "No hay datos suficientes para describir tus dias mas comprometidos."

        top = worst_days.iloc[0]
        return (
            f"El dia con peor recuperacion potencial fue {pd.to_datetime(top['metric_date']).date()}: "
            f"sueno {top['duration_hours']:.1f}h, HRV {top['overnight_avg']:.1f}, resting HR {top['resting_hr_bpm']:.1f} "
            f"y carga {top['total_training_load']:.1f}. Conviene revisar si ese patron coincide con fatiga subjetiva."
        )

    def build_alerts_narrative(self) -> str:
        alerts = self.performance.build_fatigue_alerts()
        if alerts.empty:
            return "No aparecen alertas compuestas de fatiga en el periodo actual."

        high = len(alerts[alerts["severity"] == "high"])
        medium = len(alerts[alerts["severity"] == "medium"])
        latest = alerts.sort_values("metric_date").iloc[-1]
        return (
            f"Se detectaron {len(alerts)} alertas compuestas de fatiga ({high} altas, {medium} medias). "
            f"La mas reciente fue el {latest['metric_date']} con estas senales: {latest['signals']}."
        )

    def build_weekly_markdown_report(self) -> str:
        comparison = self.performance.build_weekly_comparison()
        lines = [
            "# Weekly Garmin Insights Report",
            "",
            "## Summary",
            self.build_weekly_narrative(),
            "",
            "## Best Day",
            self.build_best_day_narrative(),
            "",
            "## Worst Day",
            self.build_worst_day_narrative(),
            "",
            "## Fatigue Alerts",
            self.build_alerts_narrative(),
            "",
            "## Weekly Comparison",
        ]
        if comparison.empty:
            lines.append("No comparison data available.")
        else:
            for _, row in comparison.iterrows():
                unit = f" {row['unit']}" if row["unit"] else ""
                lines.append(
                    f"- {row['metric']}: {row['recent']}{unit} vs {row['previous']}{unit} ({row['direction']} {row['delta']:+.2f}{unit})"
                )
        return "\n".join(lines)

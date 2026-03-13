from __future__ import annotations

import pandas as pd

from app.storage import DatabaseManager


class ManualCheckinAnalyticsService:
    def __init__(self, db: DatabaseManager | None = None) -> None:
        self.db = db or DatabaseManager()

    def load_checkins(self) -> pd.DataFrame:
        frame = self.db.read_sql("SELECT * FROM manual_checkins ORDER BY checkin_date")
        if frame.empty:
            return frame
        frame["checkin_date"] = pd.to_datetime(frame["checkin_date"])
        return frame

    def build_context_summary(self) -> str:
        frame = self.load_checkins()
        if frame.empty:
            return "Aun no hay check-ins manuales."

        recent = frame.sort_values("checkin_date").tail(7)
        parts: list[str] = []
        if "perceived_energy" in recent.columns and recent["perceived_energy"].notna().any():
            parts.append(f"energia media {recent['perceived_energy'].mean():.1f}/5")
        if "work_stress" in recent.columns and recent["work_stress"].notna().any():
            parts.append(f"estres medio {recent['work_stress'].mean():.1f}/5")
        if "muscle_soreness" in recent.columns and recent["muscle_soreness"].notna().any():
            parts.append(f"dolor muscular medio {recent['muscle_soreness'].mean():.1f}/5")
        if "mood" in recent.columns and recent["mood"].notna().any():
            parts.append(f"estado emocional medio {recent['mood'].mean():.1f}/5")
        return "Contexto manual reciente: " + (", ".join(parts) if parts else "sin suficientes escalas completadas.")

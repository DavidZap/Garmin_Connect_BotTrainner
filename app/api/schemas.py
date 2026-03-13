from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str


class MessageResponse(BaseModel):
    message: str


class RefreshRequest(BaseModel):
    days: int = 7
    source: str = "node"


class ManualCheckinRequest(BaseModel):
    checkin_date: str
    perceived_energy: int | None = None
    work_stress: int | None = None
    muscle_soreness: int | None = None
    hydration: int | None = None
    nutrition_quality: int | None = None
    mood: int | None = None
    strength_training_load: int | None = None
    menstrual_cycle_phase: str | None = None
    notes: str | None = None


class TableResponse(BaseModel):
    rows: list[dict[str, Any]]

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.analytics import AnalyticsService, CoverageAnalyticsService, ManualCheckinAnalyticsService, PerformanceAnalyticsService
from app.api.schemas import HealthResponse, ManualCheckinRequest, MessageResponse, RefreshRequest, TableResponse
from app.ingestion import IngestionService
from app.insights import InsightService, NarrativeInsightService
from app.storage import DatabaseManager


app = FastAPI(title="Garmin Insights API", version="0.1.0")
PWA_DIR = Path(__file__).resolve().parents[1] / "pwa"

app.mount("/static", StaticFiles(directory=PWA_DIR), name="static")


def _to_records(frame: pd.DataFrame) -> list[dict]:
    if frame.empty:
        return []
    current = frame.copy()
    for column in current.columns:
        if pd.api.types.is_datetime64_any_dtype(current[column]):
            current[column] = current[column].astype(str)
    return current.where(pd.notnull(current), None).to_dict(orient="records")


@app.get("/", include_in_schema=False)
def serve_pwa() -> FileResponse:
    return FileResponse(PWA_DIR / "index.html")


@app.get("/manifest.webmanifest", include_in_schema=False)
def serve_manifest() -> FileResponse:
    return FileResponse(PWA_DIR / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js", include_in_schema=False)
def serve_service_worker() -> FileResponse:
    return FileResponse(PWA_DIR / "sw.js", media_type="application/javascript")


@app.get("/icon.svg", include_in_schema=False)
def serve_icon() -> FileResponse:
    return FileResponse(PWA_DIR / "icon.svg", media_type="image/svg+xml")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", app="garmin_insights_api")


@app.get("/coverage", response_model=TableResponse)
def get_coverage() -> TableResponse:
    frame = CoverageAnalyticsService().build_coverage_report()
    return TableResponse(rows=_to_records(frame))


@app.get("/daily", response_model=TableResponse)
def get_daily(date_from: str | None = Query(default=None), date_to: str | None = Query(default=None)) -> TableResponse:
    frame = AnalyticsService().build_dashboard_dataset()
    if frame.empty:
        return TableResponse(rows=[])
    frame["metric_date"] = pd.to_datetime(frame["metric_date"])
    if date_from:
        frame = frame[frame["metric_date"] >= pd.to_datetime(date_from)]
    if date_to:
        frame = frame[frame["metric_date"] <= pd.to_datetime(date_to)]
    return TableResponse(rows=_to_records(frame.sort_values("metric_date")))


@app.get("/insights", response_model=TableResponse)
def get_insights(date_from: str | None = Query(default=None), date_to: str | None = Query(default=None)) -> TableResponse:
    db = DatabaseManager()
    frame = db.read_sql("SELECT * FROM insights_history ORDER BY insight_date DESC")
    if frame.empty:
        frame = InsightService(db).generate_insights()
    if not frame.empty and "insight_date" in frame.columns:
        frame["insight_date"] = pd.to_datetime(frame["insight_date"])
        if date_from:
            frame = frame[frame["insight_date"] >= pd.to_datetime(date_from)]
        if date_to:
            frame = frame[frame["insight_date"] <= pd.to_datetime(date_to)]
    return TableResponse(rows=_to_records(frame))


@app.get("/performance/weekly-comparison", response_model=TableResponse)
def get_weekly_comparison() -> TableResponse:
    frame = PerformanceAnalyticsService().build_weekly_comparison()
    return TableResponse(rows=_to_records(frame))


@app.get("/performance/best-days", response_model=TableResponse)
def get_best_days() -> TableResponse:
    best, _ = PerformanceAnalyticsService().build_day_rankings()
    return TableResponse(rows=_to_records(best))


@app.get("/performance/worst-days", response_model=TableResponse)
def get_worst_days() -> TableResponse:
    _, worst = PerformanceAnalyticsService().build_day_rankings()
    return TableResponse(rows=_to_records(worst))


@app.get("/performance/fatigue-alerts", response_model=TableResponse)
def get_fatigue_alerts() -> TableResponse:
    frame = PerformanceAnalyticsService().build_fatigue_alerts()
    return TableResponse(rows=_to_records(frame))


@app.get("/narrative/weekly", response_model=MessageResponse)
def get_weekly_narrative() -> MessageResponse:
    return MessageResponse(message=NarrativeInsightService().build_weekly_narrative())


@app.get("/narrative/best-day", response_model=MessageResponse)
def get_best_day_narrative() -> MessageResponse:
    return MessageResponse(message=NarrativeInsightService().build_best_day_narrative())


@app.get("/narrative/worst-day", response_model=MessageResponse)
def get_worst_day_narrative() -> MessageResponse:
    return MessageResponse(message=NarrativeInsightService().build_worst_day_narrative())


@app.get("/manual-checkins", response_model=TableResponse)
def get_manual_checkins() -> TableResponse:
    frame = ManualCheckinAnalyticsService().load_checkins()
    return TableResponse(rows=_to_records(frame))


@app.post("/manual-checkins", response_model=MessageResponse)
def create_manual_checkin(payload: ManualCheckinRequest) -> MessageResponse:
    db = DatabaseManager()
    frame = pd.DataFrame(
        [
            {
                "checkin_date": payload.checkin_date,
                "perceived_energy": payload.perceived_energy,
                "work_stress": payload.work_stress,
                "muscle_soreness": payload.muscle_soreness,
                "hydration": payload.hydration,
                "nutrition_quality": payload.nutrition_quality,
                "mood": payload.mood,
                "strength_training_load": payload.strength_training_load,
                "menstrual_cycle_phase": payload.menstrual_cycle_phase,
                "notes": payload.notes,
                "source": "manual_api",
            }
        ]
    )
    db.upsert_dataframe("manual_checkins", frame, ["checkin_date"])
    return MessageResponse(message=f"Manual check-in saved for {payload.checkin_date}")


@app.post("/refresh", response_model=MessageResponse)
def refresh_data(payload: RefreshRequest) -> MessageResponse:
    ingestion = IngestionService()
    ingestion.settings.garmin_source = payload.source
    ingestion.client = ingestion._build_client()

    counts = ingestion.ingest_last_days(payload.days)
    analytics = AnalyticsService(ingestion.db)
    derived = analytics.persist_derived_metrics()
    insights = InsightService(ingestion.db, analytics).persist_insights()
    report = NarrativeInsightService(ingestion.db).build_weekly_markdown_report()
    exports_path = ingestion.settings.exports_path
    exports_path.mkdir(parents=True, exist_ok=True)
    report_path = exports_path / "weekly_report_latest.md"
    report_path.write_text(report, encoding="utf-8")

    return MessageResponse(
        message=(
            f"Refresh completed. Ingested={counts}, derived={len(derived)}, "
            f"insights={len(insights)}, report={report_path.name}"
        )
    )


@app.get("/meta/summary", response_model=TableResponse)
def get_meta_summary() -> TableResponse:
    rows = [
        {"name": "generated_at", "value": datetime.now().isoformat()},
        {"name": "availability_summary", "value": CoverageAnalyticsService().build_availability_summary()},
        {"name": "manual_summary", "value": ManualCheckinAnalyticsService().build_context_summary()},
        {"name": "weekly_narrative", "value": NarrativeInsightService().build_weekly_narrative()},
    ]
    return TableResponse(rows=rows)

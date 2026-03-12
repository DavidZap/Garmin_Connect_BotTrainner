from __future__ import annotations

import pandas as pd


DATE_COLUMNS = {
    "daily_summary": "summary_date",
    "sleep": "sleep_date",
    "hrv": "measurement_date",
    "resting_hr": "measurement_date",
    "body_battery": "measurement_date",
    "training_readiness": "measurement_date",
    "training_status": "measurement_date",
    "activities": "activity_date",
    "weight_body_composition": "measurement_date",
}

OPTIONAL_AUDIT_COLUMNS = {
    "daily_summary": {"source", "raw_payload_path"},
    "sleep": {"source", "raw_payload_path"},
    "hrv": {"source", "raw_payload_path"},
    "resting_hr": {"source", "raw_payload_path"},
    "body_battery": {"source", "raw_payload_path"},
    "training_readiness": {"source", "raw_payload_path"},
    "training_status": {"source", "raw_payload_path"},
    "activities": {"source", "raw_payload_path"},
    "activity_details": set(),
    "weight_body_composition": {"source", "raw_payload_path"},
}


def normalize_ingested_data(
    datasets: dict[str, pd.DataFrame],
    source: str,
    raw_payload_paths: dict[str, str],
) -> dict[str, pd.DataFrame]:
    normalized: dict[str, pd.DataFrame] = {}
    for name, frame in datasets.items():
        if frame is None:
            continue
        current = frame.copy()
        if current.empty:
            normalized[name] = current
            continue

        date_column = DATE_COLUMNS.get(name)
        if date_column and date_column in current.columns:
            current[date_column] = pd.to_datetime(current[date_column]).dt.strftime("%Y-%m-%d")

        current = current.drop_duplicates()
        allowed_optional_columns = OPTIONAL_AUDIT_COLUMNS.get(name, set())
        if "source" in allowed_optional_columns:
            if "source" not in current.columns:
                current["source"] = source
            else:
                current["source"] = current["source"].fillna(source)
        if "raw_payload_path" in allowed_optional_columns:
            if "raw_payload_path" not in current.columns:
                current["raw_payload_path"] = raw_payload_paths.get(name)
            else:
                current["raw_payload_path"] = current["raw_payload_path"].fillna(raw_payload_paths.get(name))
        normalized[name] = current
    return normalized


def build_daily_analytics_frame(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    daily = frames["daily_summary"].copy()
    daily["metric_date"] = pd.to_datetime(daily["summary_date"])
    daily = daily.drop(columns=["summary_date"])

    joins = [
        ("sleep", "sleep_date"),
        ("hrv", "measurement_date"),
        ("resting_hr", "measurement_date"),
        ("body_battery", "measurement_date"),
        ("training_readiness", "measurement_date"),
        ("training_status", "measurement_date"),
        ("weight_body_composition", "measurement_date"),
    ]

    for table_name, date_column in joins:
        frame = frames.get(table_name, pd.DataFrame()).copy()
        if frame.empty:
            continue
        frame["metric_date"] = pd.to_datetime(frame[date_column])
        frame = frame.drop(columns=[col for col in [date_column, "source", "raw_payload_path", "created_at", "updated_at"] if col in frame.columns])
        daily = daily.merge(frame, on="metric_date", how="left")

    activities = frames.get("activities", pd.DataFrame()).copy()
    if not activities.empty:
        activities["metric_date"] = pd.to_datetime(activities["activity_date"])
        aggregated = (
            activities.groupby("metric_date", as_index=False)
            .agg(
                activity_count=("activity_id", "count"),
                total_duration_minutes=("duration_minutes", "sum"),
                total_distance_km=("distance_km", "sum"),
                total_training_load=("training_load", "sum"),
                avg_activity_hr=("avg_hr", "mean"),
            )
        )
        daily = daily.merge(aggregated, on="metric_date", how="left")

    numeric_columns = daily.select_dtypes(include=["number"]).columns
    daily[numeric_columns] = daily[numeric_columns].fillna(0)
    daily = daily.sort_values("metric_date").reset_index(drop=True)
    return daily

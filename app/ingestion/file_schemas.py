from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetFileSchema:
    dataset_name: str
    date_column: str | None
    required_columns: tuple[str, ...]
    optional_columns: tuple[str, ...]
    aliases: dict[str, tuple[str, ...]]


FILE_IMPORT_SCHEMAS: dict[str, DatasetFileSchema] = {
    "daily_summary": DatasetFileSchema(
        dataset_name="daily_summary",
        date_column="summary_date",
        required_columns=("summary_date",),
        optional_columns=("steps", "calories", "distance_km", "floors", "intense_minutes", "active_kcal"),
        aliases={
            "summary_date": ("date", "calendar_date"),
            "steps": ("step_count",),
            "distance_km": ("distance", "distanceKm"),
            "intense_minutes": ("intensity_minutes", "moderate_vigorous_minutes"),
        },
    ),
    "sleep": DatasetFileSchema(
        dataset_name="sleep",
        date_column="sleep_date",
        required_columns=("sleep_date",),
        optional_columns=("duration_hours", "awake_minutes", "rem_hours", "light_hours", "deep_hours", "sleep_score", "bedtime", "wake_time"),
        aliases={
            "sleep_date": ("date",),
            "duration_hours": ("sleep_hours", "duration", "total_sleep_hours"),
            "sleep_score": ("score",),
        },
    ),
    "hrv": DatasetFileSchema(
        dataset_name="hrv",
        date_column="measurement_date",
        required_columns=("measurement_date",),
        optional_columns=("overnight_avg", "baseline_low", "baseline_high", "hrv_status"),
        aliases={
            "measurement_date": ("date",),
            "overnight_avg": ("hrv", "avg_hrv", "overnight_hrv"),
            "baseline_low": ("lower_baseline",),
            "baseline_high": ("upper_baseline",),
        },
    ),
    "resting_hr": DatasetFileSchema(
        dataset_name="resting_hr",
        date_column="measurement_date",
        required_columns=("measurement_date",),
        optional_columns=("resting_hr_bpm",),
        aliases={
            "measurement_date": ("date",),
            "resting_hr_bpm": ("resting_hr", "rhr", "restingHeartRate"),
        },
    ),
    "body_battery": DatasetFileSchema(
        dataset_name="body_battery",
        date_column="measurement_date",
        required_columns=("measurement_date",),
        optional_columns=("body_battery_max", "body_battery_min", "body_battery_avg", "end_of_day_value"),
        aliases={
            "measurement_date": ("date",),
            "body_battery_avg": ("avg_body_battery", "average_body_battery"),
            "end_of_day_value": ("body_battery_end", "end_value"),
        },
    ),
    "training_readiness": DatasetFileSchema(
        dataset_name="training_readiness",
        date_column="measurement_date",
        required_columns=("measurement_date",),
        optional_columns=("readiness_score", "readiness_level", "primary_limiter"),
        aliases={
            "measurement_date": ("date",),
            "readiness_score": ("score", "training_readiness"),
            "readiness_level": ("level",),
        },
    ),
    "training_status": DatasetFileSchema(
        dataset_name="training_status",
        date_column="measurement_date",
        required_columns=("measurement_date",),
        optional_columns=("training_status", "load_ratio", "vo2max", "status_detail"),
        aliases={
            "measurement_date": ("date",),
            "training_status": ("status",),
            "vo2max": ("vo2_max",),
        },
    ),
    "activities": DatasetFileSchema(
        dataset_name="activities",
        date_column="activity_date",
        required_columns=("activity_id", "activity_date"),
        optional_columns=("start_time", "sport", "sub_sport", "duration_minutes", "distance_km", "calories", "avg_hr", "max_hr", "training_load", "avg_speed_kmh"),
        aliases={
            "activity_id": ("id", "activityId"),
            "activity_date": ("date", "start_date"),
            "start_time": ("startTime", "start_timestamp"),
            "sport": ("sport_type", "activity_type"),
            "duration_minutes": ("duration", "duration_min"),
            "distance_km": ("distance", "distanceKm"),
            "avg_hr": ("average_hr", "averageHeartRate"),
            "max_hr": ("maximum_hr", "maxHeartRate"),
            "training_load": ("load", "trainingLoad"),
            "avg_speed_kmh": ("average_speed_kmh", "avg_speed"),
        },
    ),
    "activity_details": DatasetFileSchema(
        dataset_name="activity_details",
        date_column=None,
        required_columns=("activity_id",),
        optional_columns=("elevation_gain_m", "avg_cadence", "avg_power", "aerobic_effect", "anaerobic_effect", "detail_json"),
        aliases={
            "activity_id": ("id", "activityId"),
            "elevation_gain_m": ("elevation_gain", "elevationGain"),
            "avg_cadence": ("cadence", "average_cadence"),
            "avg_power": ("power", "average_power"),
            "aerobic_effect": ("training_effect_aerobic",),
            "anaerobic_effect": ("training_effect_anaerobic",),
            "detail_json": ("details_json", "payload_json"),
        },
    ),
    "weight_body_composition": DatasetFileSchema(
        dataset_name="weight_body_composition",
        date_column="measurement_date",
        required_columns=("measurement_date",),
        optional_columns=("weight_kg", "body_fat_pct", "muscle_mass_kg", "body_water_pct", "bmi"),
        aliases={
            "measurement_date": ("date",),
            "weight_kg": ("weight", "weightKg"),
            "body_fat_pct": ("body_fat", "bodyFatPercentage"),
            "muscle_mass_kg": ("muscle_mass", "muscleMassKg"),
            "body_water_pct": ("body_water", "bodyWaterPercentage"),
        },
    ),
}

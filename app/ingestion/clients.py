from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.config import get_settings
from app.ingestion.file_schemas import FILE_IMPORT_SCHEMAS, DatasetFileSchema


DATASETS = [
    "daily_summary",
    "sleep",
    "hrv",
    "resting_hr",
    "body_battery",
    "training_readiness",
    "training_status",
    "activities",
    "activity_details",
    "weight_body_composition",
]


@dataclass
class FetchResult:
    data: dict[str, pd.DataFrame]
    raw_payload_paths: dict[str, str]
    source: str


class BaseGarminClient(ABC):
    @abstractmethod
    def fetch(self, start_date: date, end_date: date, save_raw: bool = True) -> FetchResult:
        raise NotImplementedError


class MockGarminClient(BaseGarminClient):
    def __init__(self) -> None:
        self.settings = get_settings()

    def fetch(self, start_date: date, end_date: date, save_raw: bool = True) -> FetchResult:
        dates = pd.date_range(start=start_date, end=end_date, freq="D")
        rng = np.random.default_rng(seed=42)

        daily_summary = pd.DataFrame(
            {
                "summary_date": dates.strftime("%Y-%m-%d"),
                "steps": rng.integers(3500, 18000, len(dates)),
                "calories": rng.integers(1800, 3200, len(dates)),
                "distance_km": np.round(rng.uniform(2.0, 18.0, len(dates)), 2),
                "floors": rng.integers(0, 25, len(dates)),
                "intense_minutes": rng.integers(0, 120, len(dates)),
                "active_kcal": rng.integers(200, 1200, len(dates)),
            }
        )

        sleep = pd.DataFrame(
            {
                "sleep_date": dates.strftime("%Y-%m-%d"),
                "duration_hours": np.round(rng.normal(7.1, 0.9, len(dates)).clip(4.5, 9.5), 2),
                "awake_minutes": rng.integers(10, 90, len(dates)),
                "rem_hours": np.round(rng.uniform(0.8, 2.0, len(dates)), 2),
                "light_hours": np.round(rng.uniform(2.5, 4.5, len(dates)), 2),
                "deep_hours": np.round(rng.uniform(0.6, 1.8, len(dates)), 2),
                "sleep_score": np.round(rng.normal(75, 10, len(dates)).clip(40, 95), 1),
                "bedtime": [
                    (datetime.combine(d.date(), datetime.min.time()) + timedelta(hours=22, minutes=int(rng.integers(0, 90)))).isoformat()
                    for d in dates
                ],
                "wake_time": [
                    (datetime.combine(d.date(), datetime.min.time()) + timedelta(days=1, hours=5, minutes=int(rng.integers(30, 150)))).isoformat()
                    for d in dates
                ],
            }
        )

        hrv_values = np.round(rng.normal(55, 10, len(dates)).clip(25, 95), 1)
        hrv = pd.DataFrame(
            {
                "measurement_date": dates.strftime("%Y-%m-%d"),
                "overnight_avg": hrv_values,
                "baseline_low": 45.0,
                "baseline_high": 65.0,
                "hrv_status": ["balanced" if 45 <= value <= 65 else "unbalanced" for value in hrv_values],
            }
        )

        resting_hr = pd.DataFrame(
            {
                "measurement_date": dates.strftime("%Y-%m-%d"),
                "resting_hr_bpm": np.round(rng.normal(51, 5, len(dates)).clip(42, 70), 1),
            }
        )

        body_battery = pd.DataFrame(
            {
                "measurement_date": dates.strftime("%Y-%m-%d"),
                "body_battery_max": np.round(rng.normal(82, 8, len(dates)).clip(50, 100), 1),
                "body_battery_min": np.round(rng.normal(18, 8, len(dates)).clip(5, 50), 1),
                "body_battery_avg": np.round(rng.normal(46, 10, len(dates)).clip(10, 85), 1),
                "end_of_day_value": np.round(rng.normal(28, 8, len(dates)).clip(5, 60), 1),
            }
        )

        readiness_scores = np.round(rng.normal(63, 16, len(dates)).clip(5, 100), 1)
        training_readiness = pd.DataFrame(
            {
                "measurement_date": dates.strftime("%Y-%m-%d"),
                "readiness_score": readiness_scores,
                "readiness_level": pd.cut(
                    readiness_scores,
                    bins=[0, 25, 50, 75, 100],
                    labels=["very_low", "low", "moderate", "high"],
                    include_lowest=True,
                ).astype(str),
                "primary_limiter": rng.choice(["sleep", "load", "stress", "recovery", "balanced"], len(dates)),
            }
        )

        training_status = pd.DataFrame(
            {
                "measurement_date": dates.strftime("%Y-%m-%d"),
                "training_status": rng.choice(["productive", "maintaining", "recovery", "strained", "peaking"], len(dates)),
                "load_ratio": np.round(rng.normal(1.0, 0.2, len(dates)).clip(0.4, 1.8), 2),
                "vo2max": np.round(rng.normal(48, 4, len(dates)).clip(38, 60), 1),
                "status_detail": rng.choice(
                    [
                        "Carga alineada con la condicion.",
                        "Ligera fatiga acumulada.",
                        "Buena adaptacion reciente.",
                        "Conviene priorizar recuperacion.",
                    ],
                    len(dates),
                ),
            }
        )

        weights = pd.DataFrame(
            {
                "measurement_date": dates.strftime("%Y-%m-%d"),
                "weight_kg": np.round(rng.normal(72, 1.2, len(dates)).clip(69, 76), 2),
                "body_fat_pct": np.round(rng.normal(16, 1.0, len(dates)).clip(12, 20), 2),
                "muscle_mass_kg": np.round(rng.normal(33, 0.6, len(dates)).clip(31, 35), 2),
                "body_water_pct": np.round(rng.normal(58, 1.5, len(dates)).clip(54, 62), 2),
                "bmi": np.round(rng.normal(23.2, 0.3, len(dates)).clip(22, 24.5), 2),
            }
        )

        activity_rows: list[dict[str, Any]] = []
        activity_detail_rows: list[dict[str, Any]] = []
        sports = ["running", "cycling", "strength_training", "walking", "trail_running"]
        for current_date in dates:
            for idx in range(int(rng.integers(0, 3))):
                activity_id = f"{current_date.strftime('%Y%m%d')}-{idx}"
                duration_minutes = float(np.round(rng.uniform(25, 140), 1))
                distance_km = float(np.round(max(0.0, rng.normal(9, 6)), 2))
                training_load = float(np.round(rng.uniform(20, 220), 1))
                activity_rows.append(
                    {
                        "activity_id": activity_id,
                        "activity_date": current_date.strftime("%Y-%m-%d"),
                        "start_time": (datetime.combine(current_date.date(), datetime.min.time()) + timedelta(hours=6 + idx * 6)).isoformat(),
                        "sport": str(rng.choice(sports)),
                        "sub_sport": None,
                        "duration_minutes": duration_minutes,
                        "distance_km": distance_km,
                        "calories": int(rng.integers(180, 1400)),
                        "avg_hr": float(np.round(rng.normal(142, 15), 1)),
                        "max_hr": float(np.round(rng.normal(172, 10), 1)),
                        "training_load": training_load,
                        "avg_speed_kmh": float(np.round(distance_km / max(duration_minutes / 60.0, 0.1), 2)),
                    }
                )
                activity_detail_rows.append(
                    {
                        "activity_id": activity_id,
                        "elevation_gain_m": float(np.round(rng.uniform(0, 800), 1)),
                        "avg_cadence": float(np.round(rng.uniform(70, 180), 1)),
                        "avg_power": float(np.round(rng.uniform(100, 320), 1)),
                        "aerobic_effect": float(np.round(rng.uniform(1.0, 5.0), 1)),
                        "anaerobic_effect": float(np.round(rng.uniform(0.0, 4.0), 1)),
                        "detail_json": json.dumps({"device": "mock", "notes": "Generated sample"}),
                    }
                )

        activities = pd.DataFrame(activity_rows)
        activity_details = pd.DataFrame(activity_detail_rows)
        if activities.empty:
            activities = pd.DataFrame(columns=["activity_id", "activity_date", "start_time", "sport", "sub_sport", "duration_minutes", "distance_km", "calories", "avg_hr", "max_hr", "training_load", "avg_speed_kmh"])
            activity_details = pd.DataFrame(columns=["activity_id", "elevation_gain_m", "avg_cadence", "avg_power", "aerobic_effect", "anaerobic_effect", "detail_json"])

        datasets = {
            "daily_summary": daily_summary,
            "sleep": sleep,
            "hrv": hrv,
            "resting_hr": resting_hr,
            "body_battery": body_battery,
            "training_readiness": training_readiness,
            "training_status": training_status,
            "activities": activities,
            "activity_details": activity_details,
            "weight_body_composition": weights,
        }

        raw_payload_paths = self._save_raw_payloads(datasets) if save_raw else {}
        return FetchResult(data=datasets, raw_payload_paths=raw_payload_paths, source="mock")

    def _save_raw_payloads(self, datasets: dict[str, pd.DataFrame]) -> dict[str, str]:
        self.settings.raw_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_paths: dict[str, str] = {}
        for dataset_name, frame in datasets.items():
            output_path = self.settings.raw_path / f"{timestamp}_{dataset_name}.json"
            frame.to_json(output_path, orient="records", indent=2)
            saved_paths[dataset_name] = str(output_path)
        return saved_paths


class FileImportGarminClient(BaseGarminClient):
    def __init__(self, import_dir: str | Path) -> None:
        self.import_dir = Path(import_dir)

    def fetch(self, start_date: date, end_date: date, save_raw: bool = True) -> FetchResult:
        datasets: dict[str, pd.DataFrame] = {}
        raw_paths: dict[str, str] = {}
        for dataset_name in DATASETS:
            csv_path = self.import_dir / f"{dataset_name}.csv"
            json_path = self.import_dir / f"{dataset_name}.json"
            if csv_path.exists():
                datasets[dataset_name] = self._normalize_imported_frame(dataset_name, pd.read_csv(csv_path), start_date, end_date)
                raw_paths[dataset_name] = str(csv_path)
            elif json_path.exists():
                datasets[dataset_name] = self._normalize_imported_frame(dataset_name, pd.read_json(json_path), start_date, end_date)
                raw_paths[dataset_name] = str(json_path)
            else:
                datasets[dataset_name] = pd.DataFrame()
        return FetchResult(data=datasets, raw_payload_paths=raw_paths, source="file_import")

    def _normalize_imported_frame(
        self,
        dataset_name: str,
        frame: pd.DataFrame,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        if frame.empty:
            return frame

        schema = FILE_IMPORT_SCHEMAS.get(dataset_name)
        if schema is None:
            return frame

        current = frame.copy()
        current.columns = [str(column).strip() for column in current.columns]
        current = self._apply_aliases(current, schema)
        current = self._keep_supported_columns(current, schema)

        missing_required = [column for column in schema.required_columns if column not in current.columns]
        if missing_required:
            raise ValueError(
                f"El archivo para '{dataset_name}' no contiene las columnas requeridas: {', '.join(missing_required)}."
            )

        if schema.date_column and schema.date_column in current.columns:
            current[schema.date_column] = pd.to_datetime(current[schema.date_column], errors="coerce")
            current = current.dropna(subset=[schema.date_column])
            current = current[
                (current[schema.date_column].dt.date >= start_date)
                & (current[schema.date_column].dt.date <= end_date)
            ]
            current[schema.date_column] = current[schema.date_column].dt.strftime("%Y-%m-%d")

        if dataset_name == "activity_details" and "detail_json" in current.columns:
            current["detail_json"] = current["detail_json"].apply(self._ensure_json_string)

        return current

    @staticmethod
    def _apply_aliases(frame: pd.DataFrame, schema: DatasetFileSchema) -> pd.DataFrame:
        current = frame.copy()
        rename_map: dict[str, str] = {}
        for canonical_name, aliases in schema.aliases.items():
            if canonical_name in current.columns:
                continue
            for alias in aliases:
                if alias in current.columns:
                    rename_map[alias] = canonical_name
                    break
        return current.rename(columns=rename_map)

    @staticmethod
    def _keep_supported_columns(frame: pd.DataFrame, schema: DatasetFileSchema) -> pd.DataFrame:
        supported_columns = set(schema.required_columns) | set(schema.optional_columns)
        selected = [column for column in frame.columns if column in supported_columns]
        return frame[selected].copy()

    @staticmethod
    def _ensure_json_string(value: Any) -> str:
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=True)

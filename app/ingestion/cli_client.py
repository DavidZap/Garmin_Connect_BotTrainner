from __future__ import annotations

import json
import subprocess
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import get_settings
from app.ingestion.clients import BaseGarminClient, FetchResult
from app.utils import get_logger


logger = get_logger(__name__)


class GarminCliClient(BaseGarminClient):
    def __init__(self, command: str | None = None) -> None:
        self.settings = get_settings()
        self.command = command or self.settings.garmin_cli_command

    def fetch(self, start_date: date, end_date: date, save_raw: bool = True) -> FetchResult:
        raw_payloads: dict[str, Any] = {}

        activities_payload = self._run_json(["activities", "list", "--after", start_date.isoformat(), "--before", end_date.isoformat(), "--limit", "1000"])
        raw_payloads["activities"] = activities_payload

        activity_rows = self._parse_activities(activities_payload)
        activity_detail_rows = self._fetch_activity_details(activity_rows)

        daily_rows: list[dict[str, Any]] = []
        sleep_rows: list[dict[str, Any]] = []
        hrv_rows: list[dict[str, Any]] = []
        rhr_rows: list[dict[str, Any]] = []
        body_battery_rows: list[dict[str, Any]] = []
        readiness_rows: list[dict[str, Any]] = []
        training_status_rows: list[dict[str, Any]] = []

        for current_date in pd.date_range(start=start_date, end=end_date, freq="D"):
            current = current_date.date()
            date_str = current.isoformat()

            steps_payload = self._run_json(["health", "steps", "--date", date_str], tolerate_error=True)
            sleep_payload = self._run_json(["health", "sleep", "--date", date_str], tolerate_error=True)
            rhr_payload = self._run_json(["health", "rhr", "--date", date_str], tolerate_error=True)
            body_battery_payload = self._run_json(["health", "body-battery", "--date", date_str], tolerate_error=True)
            readiness_payload = self._run_json(["training", "readiness", "--date", date_str], tolerate_error=True)
            status_payload = self._run_json(["training", "status", "--date", date_str], tolerate_error=True)
            hrv_payload = self._run_json(["training", "hrv", "--date", date_str], tolerate_error=True)

            raw_payloads[f"daily_summary_{date_str}"] = steps_payload
            raw_payloads[f"sleep_{date_str}"] = sleep_payload
            raw_payloads[f"resting_hr_{date_str}"] = rhr_payload
            raw_payloads[f"body_battery_{date_str}"] = body_battery_payload
            raw_payloads[f"training_readiness_{date_str}"] = readiness_payload
            raw_payloads[f"training_status_{date_str}"] = status_payload
            raw_payloads[f"hrv_{date_str}"] = hrv_payload

            daily_rows.append(self._parse_daily_steps(date_str, steps_payload))
            sleep_rows.append(self._parse_sleep(date_str, sleep_payload))
            rhr_rows.append(self._parse_resting_hr(date_str, rhr_payload))
            body_battery_rows.append(self._parse_body_battery(date_str, body_battery_payload))
            readiness_rows.append(self._parse_training_readiness(date_str, readiness_payload))
            training_status_rows.append(self._parse_training_status(date_str, status_payload))
            hrv_rows.append(self._parse_hrv(date_str, hrv_payload))

        weight_payload = self._run_json(["weight", "list", "--start", start_date.isoformat(), "--end", end_date.isoformat()], tolerate_error=True)
        raw_payloads["weight_body_composition"] = weight_payload
        weight_rows = self._parse_weight(weight_payload)

        raw_paths = self._save_raw_payloads(raw_payloads) if save_raw else {}
        return FetchResult(
            data={
                "daily_summary": pd.DataFrame(daily_rows),
                "sleep": pd.DataFrame(sleep_rows),
                "hrv": pd.DataFrame(hrv_rows),
                "resting_hr": pd.DataFrame(rhr_rows),
                "body_battery": pd.DataFrame(body_battery_rows),
                "training_readiness": pd.DataFrame(readiness_rows),
                "training_status": pd.DataFrame(training_status_rows),
                "activities": pd.DataFrame(activity_rows),
                "activity_details": pd.DataFrame(activity_detail_rows),
                "weight_body_composition": pd.DataFrame(weight_rows),
            },
            raw_payload_paths=raw_paths,
            source="garmin_cli",
        )

    def _run_json(self, args: list[str], tolerate_error: bool = False) -> Any:
        command = [self.command, *args]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "unknown CLI error"
            if tolerate_error:
                logger.warning("CLI command failed: %s | %s", " ".join(command), message)
                return {}
            raise RuntimeError(f"CLI command failed: {' '.join(command)} | {message}")

        output = result.stdout.strip()
        if not output:
            return {}
        try:
            return json.loads(output)
        except json.JSONDecodeError as exc:
            if tolerate_error:
                logger.warning("CLI output is not valid JSON for command: %s", " ".join(command))
                return {}
            raise RuntimeError(f"CLI output is not valid JSON for {' '.join(command)}") from exc

    def _fetch_activity_details(self, activities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        details: list[dict[str, Any]] = []
        for activity in activities:
            activity_id = activity.get("activity_id")
            if not activity_id:
                continue
            payload = self._run_json(["activities", "get", str(activity_id), "--details"], tolerate_error=True)
            details.append(self._parse_activity_detail(str(activity_id), payload))
        return details

    def _save_raw_payloads(self, payloads: dict[str, Any]) -> dict[str, str]:
        self.settings.raw_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_paths: dict[str, str] = {}
        for name, payload in payloads.items():
            output_path = self.settings.raw_path / f"{timestamp}_{name}.json"
            output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
            saved_paths[name] = str(output_path)
        return saved_paths

    def _parse_activities(self, payload: Any) -> list[dict[str, Any]]:
        items = payload if isinstance(payload, list) else payload.get("activities", []) if isinstance(payload, dict) else []
        rows: list[dict[str, Any]] = []
        for item in items:
            activity_id = self._get_first(item, ["activityId", "activity_id", "id"])
            start_time = self._get_first(item, ["startTimeLocal", "start_time", "startTimeGMT", "startTime"])
            activity_date = self._extract_date(start_time) or self._get_first(item, ["date", "activityDate"])
            duration_seconds = self._get_first(item, ["duration", "durationSeconds"])
            distance_m = self._get_first(item, ["distance", "distanceMeters"])
            rows.append(
                {
                    "activity_id": str(activity_id) if activity_id is not None else None,
                    "activity_date": activity_date,
                    "start_time": start_time,
                    "sport": self._extract_sport(item),
                    "sub_sport": self._get_first(item, ["subSportType", "sub_sport"]),
                    "duration_minutes": self._seconds_to_minutes(duration_seconds),
                    "distance_km": self._meters_to_km(distance_m),
                    "calories": self._get_first(item, ["calories", "activeKilocalories"]),
                    "avg_hr": self._get_first(item, ["averageHR", "avg_hr", "averageHeartRate"]),
                    "max_hr": self._get_first(item, ["maxHR", "max_hr", "maxHeartRate"]),
                    "training_load": self._get_first(item, ["trainingLoad", "load", "activityTrainingLoad"]),
                    "avg_speed_kmh": self._mps_to_kmh(self._get_first(item, ["averageSpeed", "avg_speed"])),
                }
            )
        return [row for row in rows if row.get("activity_id") and row.get("activity_date")]

    def _parse_activity_detail(self, activity_id: str, payload: Any) -> dict[str, Any]:
        summary = payload.get("summaryDTO", payload) if isinstance(payload, dict) else {}
        return {
            "activity_id": activity_id,
            "elevation_gain_m": self._get_first(summary, ["elevationGain", "totalElevationGain"]),
            "avg_cadence": self._get_first(summary, ["averageRunCadenceInStepsPerMinute", "averageCadence"]),
            "avg_power": self._get_first(summary, ["averagePower", "avgPower"]),
            "aerobic_effect": self._get_first(summary, ["aerobicTrainingEffect", "aerobicEffect"]),
            "anaerobic_effect": self._get_first(summary, ["anaerobicTrainingEffect", "anaerobicEffect"]),
            "detail_json": json.dumps(payload, ensure_ascii=True),
        }

    def _parse_daily_steps(self, date_str: str, payload: Any) -> dict[str, Any]:
        return {
            "summary_date": date_str,
            "steps": self._get_first(payload, ["totalSteps", "steps", "stepCount"]) or 0,
            "calories": self._get_first(payload, ["totalKilocalories", "calories"]) or 0,
            "distance_km": self._meters_to_km(self._get_first(payload, ["totalDistanceMeters", "distance"])) or 0,
            "floors": self._get_first(payload, ["floorsClimbed", "floors"]) or 0,
            "intense_minutes": self._get_first(payload, ["intensityMinutes", "activeMinutes"]) or 0,
            "active_kcal": self._get_first(payload, ["activeKilocalories", "activeCalories"]) or 0,
        }

    def _parse_sleep(self, date_str: str, payload: Any) -> dict[str, Any]:
        sleep = payload.get("dailySleepDTO", payload) if isinstance(payload, dict) else {}
        return {
            "sleep_date": date_str,
            "duration_hours": self._seconds_to_hours(self._get_first(sleep, ["sleepTimeSeconds", "sleepTime", "duration"])),
            "awake_minutes": self._seconds_to_minutes(self._get_first(sleep, ["awakeSleepSeconds", "awakeTime"])) or 0,
            "rem_hours": self._seconds_to_hours(self._get_first(sleep, ["remSleepSeconds", "remTime"])) or 0,
            "light_hours": self._seconds_to_hours(self._get_first(sleep, ["lightSleepSeconds", "lightTime"])) or 0,
            "deep_hours": self._seconds_to_hours(self._get_first(sleep, ["deepSleepSeconds", "deepTime"])) or 0,
            "sleep_score": self._get_first(sleep, ["sleepScore", "score"]),
            "bedtime": self._get_first(sleep, ["sleepStartTimestampLocal", "bedTime", "bedtime"]),
            "wake_time": self._get_first(sleep, ["sleepEndTimestampLocal", "wakeTime", "wake_time"]),
        }

    def _parse_resting_hr(self, date_str: str, payload: Any) -> dict[str, Any]:
        return {
            "measurement_date": date_str,
            "resting_hr_bpm": self._get_first(payload, ["restingHeartRate", "value", "resting_hr_bpm", "rhr"]),
        }

    def _parse_body_battery(self, date_str: str, payload: Any) -> dict[str, Any]:
        values = self._collect_numeric_values(payload, {"bodyBattery", "value", "body_battery"})
        return {
            "measurement_date": date_str,
            "body_battery_max": max(values) if values else None,
            "body_battery_min": min(values) if values else None,
            "body_battery_avg": round(sum(values) / len(values), 2) if values else None,
            "end_of_day_value": values[-1] if values else None,
        }

    def _parse_training_readiness(self, date_str: str, payload: Any) -> dict[str, Any]:
        return {
            "measurement_date": date_str,
            "readiness_score": self._get_first(payload, ["score", "readinessScore", "value"]),
            "readiness_level": self._get_first(payload, ["level", "readinessLevel", "status"]),
            "primary_limiter": self._get_first(payload, ["primaryLimiter", "limiter", "focus"]),
        }

    def _parse_training_status(self, date_str: str, payload: Any) -> dict[str, Any]:
        return {
            "measurement_date": date_str,
            "training_status": self._get_first(payload, ["trainingStatus", "status", "label"]),
            "load_ratio": self._get_first(payload, ["loadRatio", "trainingLoadRatio"]),
            "vo2max": self._get_first(payload, ["vo2Max", "vo2max"]),
            "status_detail": self._get_first(payload, ["statusDetail", "message", "description"]),
        }

    def _parse_hrv(self, date_str: str, payload: Any) -> dict[str, Any]:
        hrv_status = payload.get("hrvStatus", payload) if isinstance(payload, dict) else {}
        return {
            "measurement_date": date_str,
            "overnight_avg": self._get_first(hrv_status, ["overnightAvg", "weeklyAvg", "average"]),
            "baseline_low": self._get_first(hrv_status, ["baselineLow", "lowerBaseline"]),
            "baseline_high": self._get_first(hrv_status, ["baselineHigh", "upperBaseline"]),
            "hrv_status": self._get_first(hrv_status, ["status", "hrvStatus"]),
        }

    def _parse_weight(self, payload: Any) -> list[dict[str, Any]]:
        items = payload if isinstance(payload, list) else payload.get("weights", []) if isinstance(payload, dict) else []
        rows: list[dict[str, Any]] = []
        for item in items:
            timestamp = self._get_first(item, ["date", "measurementTime", "calendarDate"])
            rows.append(
                {
                    "measurement_date": self._extract_date(timestamp) or timestamp,
                    "weight_kg": self._get_first(item, ["weight", "weightKg"]),
                    "body_fat_pct": self._get_first(item, ["bodyFat", "bodyFatPercentage"]),
                    "muscle_mass_kg": self._get_first(item, ["muscleMass", "muscleMassKg"]),
                    "body_water_pct": self._get_first(item, ["bodyWater", "bodyWaterPercentage"]),
                    "bmi": self._get_first(item, ["bmi", "BMI"]),
                }
            )
        return [row for row in rows if row.get("measurement_date")]

    @staticmethod
    def _get_first(payload: Any, keys: list[str]) -> Any:
        if not isinstance(payload, dict):
            return None
        for key in keys:
            if key in payload and payload[key] is not None:
                return payload[key]
        return None

    @staticmethod
    def _collect_numeric_values(payload: Any, accepted_keys: set[str]) -> list[float]:
        values: list[float] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    if key in accepted_keys and isinstance(value, (int, float)):
                        values.append(float(value))
                    else:
                        walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(payload)
        return values

    @staticmethod
    def _extract_sport(payload: dict[str, Any]) -> Any:
        activity_type = payload.get("activityType")
        if isinstance(activity_type, dict):
            return activity_type.get("typeKey") or activity_type.get("typeId")
        return payload.get("sport") or payload.get("activityType")

    @staticmethod
    def _extract_date(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value)
        if "T" in text:
            return text.split("T", 1)[0]
        if " " in text:
            return text.split(" ", 1)[0]
        return text[:10] if len(text) >= 10 else text

    @staticmethod
    def _seconds_to_minutes(value: Any) -> float | None:
        if value is None:
            return None
        return round(float(value) / 60.0, 2)

    @staticmethod
    def _seconds_to_hours(value: Any) -> float | None:
        if value is None:
            return None
        return round(float(value) / 3600.0, 2)

    @staticmethod
    def _meters_to_km(value: Any) -> float | None:
        if value is None:
            return None
        return round(float(value) / 1000.0, 2)

    @staticmethod
    def _mps_to_kmh(value: Any) -> float | None:
        if value is None:
            return None
        return round(float(value) * 3.6, 2)

SCHEMA_SQL = [
    """
    CREATE TABLE IF NOT EXISTS daily_summary (
        summary_date TEXT PRIMARY KEY,
        steps INTEGER,
        calories INTEGER,
        distance_km REAL,
        floors INTEGER,
        intense_minutes INTEGER,
        active_kcal INTEGER,
        source TEXT,
        raw_payload_path TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sleep (
        sleep_date TEXT PRIMARY KEY,
        duration_hours REAL,
        awake_minutes INTEGER,
        rem_hours REAL,
        light_hours REAL,
        deep_hours REAL,
        sleep_score REAL,
        bedtime TEXT,
        wake_time TEXT,
        source TEXT,
        raw_payload_path TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS hrv (
        measurement_date TEXT PRIMARY KEY,
        overnight_avg REAL,
        baseline_low REAL,
        baseline_high REAL,
        hrv_status TEXT,
        source TEXT,
        raw_payload_path TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS resting_hr (
        measurement_date TEXT PRIMARY KEY,
        resting_hr_bpm REAL,
        source TEXT,
        raw_payload_path TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS body_battery (
        measurement_date TEXT PRIMARY KEY,
        body_battery_max REAL,
        body_battery_min REAL,
        body_battery_avg REAL,
        end_of_day_value REAL,
        source TEXT,
        raw_payload_path TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS training_readiness (
        measurement_date TEXT PRIMARY KEY,
        readiness_score REAL,
        readiness_level TEXT,
        primary_limiter TEXT,
        source TEXT,
        raw_payload_path TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS training_status (
        measurement_date TEXT PRIMARY KEY,
        training_status TEXT,
        load_ratio REAL,
        vo2max REAL,
        status_detail TEXT,
        source TEXT,
        raw_payload_path TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS activities (
        activity_id TEXT PRIMARY KEY,
        activity_date TEXT,
        start_time TEXT,
        sport TEXT,
        sub_sport TEXT,
        duration_minutes REAL,
        distance_km REAL,
        calories INTEGER,
        avg_hr REAL,
        max_hr REAL,
        training_load REAL,
        avg_speed_kmh REAL,
        source TEXT,
        raw_payload_path TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS activity_details (
        activity_id TEXT PRIMARY KEY,
        elevation_gain_m REAL,
        avg_cadence REAL,
        avg_power REAL,
        aerobic_effect REAL,
        anaerobic_effect REAL,
        detail_json TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(activity_id) REFERENCES activities(activity_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS weight_body_composition (
        measurement_date TEXT PRIMARY KEY,
        weight_kg REAL,
        body_fat_pct REAL,
        muscle_mass_kg REAL,
        body_water_pct REAL,
        bmi REAL,
        source TEXT,
        raw_payload_path TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS derived_metrics (
        metric_date TEXT PRIMARY KEY,
        sleep_hours_7d REAL,
        sleep_hours_28d REAL,
        hrv_7d REAL,
        hrv_28d REAL,
        resting_hr_7d REAL,
        resting_hr_28d REAL,
        training_load_7d REAL,
        training_load_28d REAL,
        acute_chronic_ratio REAL,
        sleep_variation_day REAL,
        sleep_variation_week REAL,
        hrv_rhr_ratio REAL,
        load_readiness_ratio REAL,
        sleep_consistency_score REAL,
        fatigue_flag INTEGER,
        fatigue_streak INTEGER,
        recovery_streak INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS manual_checkins (
        checkin_date TEXT PRIMARY KEY,
        perceived_energy INTEGER,
        work_stress INTEGER,
        muscle_soreness INTEGER,
        hydration INTEGER,
        nutrition_quality INTEGER,
        mood INTEGER,
        strength_training_load INTEGER,
        menstrual_cycle_phase TEXT,
        notes TEXT,
        source TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS insights_history (
        insight_id TEXT PRIMARY KEY,
        insight_date TEXT,
        insight_name TEXT,
        severity TEXT,
        explanation TEXT,
        recommendation TEXT,
        metric_date TEXT,
        payload_json TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """,
]

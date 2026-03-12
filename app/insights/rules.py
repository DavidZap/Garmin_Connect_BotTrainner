from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InsightRuleDefinition:
    name: str
    logic: str
    severity_levels: str
    explanation_template: str
    recommendation: str


INSIGHT_RULES = [
    InsightRuleDefinition(
        name="hrv_drop_vs_baseline",
        logic="overnight_avg < 0.92 * hrv_7d or overnight_avg < 0.88 * hrv_28d",
        severity_levels="medium/high",
        explanation_template="Tu HRV de {overnight_avg} esta por debajo de tus lineas base recientes ({hrv_7d} 7d, {hrv_28d} 28d).",
        recommendation="Reduce intensidad o prioriza recuperacion activa.",
    ),
    InsightRuleDefinition(
        name="resting_hr_increase_vs_baseline",
        logic="resting_hr_bpm > 1.05 * resting_hr_7d",
        severity_levels="medium",
        explanation_template="Tu resting HR de {resting_hr_bpm} esta por encima de la media de 7 dias ({resting_hr_7d}).",
        recommendation="Revisa estres, sueno e hidratacion antes de otra sesion exigente.",
    ),
    InsightRuleDefinition(
        name="insufficient_sleep_before_high_load",
        logic="duration_hours < 6.5 and total_training_load > training_load_7d / 7",
        severity_levels="medium/high",
        explanation_template="Dormiste {duration_hours}h antes de una jornada con carga alta ({total_training_load}).",
        recommendation="Evita encadenar otra carga alta sin mejorar el descanso.",
    ),
    InsightRuleDefinition(
        name="persistent_low_readiness",
        logic="readiness_score < 45 for >= 3 days",
        severity_levels="high",
        explanation_template="El readiness lleva varios dias en zona baja y hoy marca {readiness_score}.",
        recommendation="Prioriza recuperacion, baja volumen y vigila sintomas subjetivos.",
    ),
    InsightRuleDefinition(
        name="multi_day_fatigue_signals",
        logic="fatigue_streak >= 3",
        severity_levels="high",
        explanation_template="Acumulas {fatigue_streak} dias seguidos con senales de fatiga potencial.",
        recommendation="Introduce descarga, sueno extra y seguimiento cercano de HRV/RHR.",
    ),
    InsightRuleDefinition(
        name="balanced_load_recovery_week",
        logic="readiness_score >= 60 and acute_chronic_ratio between 0.8 and 1.2 and duration_hours >= sleep_hours_7d",
        severity_levels="positive",
        explanation_template="La combinacion de carga, sueno y readiness luce equilibrada en esta ventana.",
        recommendation="Mantener progresion gradual y consistencia de habitos.",
    ),
]


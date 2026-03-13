from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app.analytics import AnalyticsService, CoverageAnalyticsService, ManualCheckinAnalyticsService, PerformanceAnalyticsService
from app.storage import DatabaseManager
from app.insights import InsightService, NarrativeInsightService


st.set_page_config(page_title="Garmin Insights", layout="wide")

METRIC_GLOSSARY = {
    "duration_hours": {
        "label": "Horas de sueno",
        "definition": "Tiempo total de sueno registrado durante la noche.",
        "type": "Garmin real",
    },
    "sleep_score": {
        "label": "Sleep score",
        "definition": "Puntaje de calidad de sueno generado por Garmin si el dispositivo lo soporta.",
        "type": "Garmin real",
    },
    "overnight_avg": {
        "label": "HRV nocturna",
        "definition": "Promedio nocturno de variabilidad de frecuencia cardiaca. Se interpreta contra tu propia linea base.",
        "type": "Garmin real",
    },
    "baseline_low": {
        "label": "HRV baseline low",
        "definition": "Limite inferior de tu banda base reciente de HRV.",
        "type": "Garmin real",
    },
    "baseline_high": {
        "label": "HRV baseline high",
        "definition": "Limite superior de tu banda base reciente de HRV.",
        "type": "Garmin real",
    },
    "hrv_status": {
        "label": "HRV status",
        "definition": "Etiqueta Garmin para resumir si tu HRV reciente esta dentro o fuera de tu normalidad.",
        "type": "Garmin real",
    },
    "resting_hr_bpm": {
        "label": "Resting HR",
        "definition": "Frecuencia cardiaca en reposo. Suele ser mas util en tendencia que como valor aislado.",
        "type": "Garmin real",
    },
    "body_battery_avg": {
        "label": "Body Battery promedio",
        "definition": "Score propietario de Garmin sobre reservas energeticas. Util como apoyo, no como verdad fisiologica absoluta.",
        "type": "Garmin real",
    },
    "readiness_score": {
        "label": "Training Readiness",
        "definition": "Score Garmin de preparacion para entrenar. En tu cuenta actual no esta disponible por esta via.",
        "type": "No disponible hoy",
    },
    "training_status": {
        "label": "Training Status",
        "definition": "Estado global de entrenamiento segun Garmin. En tu cuenta actual no esta disponible por esta via.",
        "type": "No disponible hoy",
    },
    "total_training_load": {
        "label": "Carga diaria",
        "definition": "Suma diaria estimada de carga derivada de tus actividades registradas.",
        "type": "Derivada local",
    },
    "acute_chronic_ratio": {
        "label": "Ratio agudo/cronica",
        "definition": "Relacion entre carga reciente y carga de fondo para vigilar subidas demasiado rapidas.",
        "type": "Derivada local",
    },
    "sleep_consistency_score": {
        "label": "Consistencia del sueno",
        "definition": "Metrica derivada local sobre estabilidad de tus horas de sueno recientes.",
        "type": "Derivada local",
    },
}


@st.cache_data
def load_dashboard_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str, str, str]:
    analytics = AnalyticsService()
    coverage = CoverageAnalyticsService(analytics.db)
    performance = PerformanceAnalyticsService(analytics.db, analytics)
    manual = ManualCheckinAnalyticsService(analytics.db)
    insights = InsightService(analytics=analytics)
    narrative = NarrativeInsightService(analytics.db, performance)
    dataset = analytics.build_dashboard_dataset()
    insight_frame = analytics.db.read_sql("SELECT * FROM insights_history ORDER BY insight_date DESC")
    if insight_frame.empty:
        insight_frame = insights.generate_insights()
    coverage_frame = coverage.build_coverage_report()
    manual_checkins = manual.load_checkins()
    best_days, worst_days = performance.build_day_rankings()
    weekly_comparison = performance.build_weekly_comparison()
    fatigue_alerts = performance.build_fatigue_alerts()
    return (
        dataset,
        insight_frame,
        coverage_frame,
        manual_checkins,
        insights.build_daily_summary_text(),
        insights.build_weekly_summary_text(),
        best_days,
        worst_days,
        weekly_comparison,
        fatigue_alerts,
        narrative.build_weekly_narrative(),
        narrative.build_best_day_narrative(),
        narrative.build_worst_day_narrative(),
        narrative.build_alerts_narrative(),
    )


def render_metrics_row(dataset: pd.DataFrame) -> None:
    latest = dataset.sort_values("metric_date").iloc[-1]
    cols = st.columns(5)
    cols[0].metric("Sueno (h)", f"{latest.get('duration_hours', 0):.1f}")
    cols[1].metric("HRV", f"{latest.get('overnight_avg', 0):.1f}")
    cols[2].metric("Resting HR", f"{latest.get('resting_hr_bpm', 0):.1f}")
    cols[3].metric("Pasos", f"{int(latest.get('steps', 0))}")
    cols[4].metric("Carga", f"{latest.get('total_training_load', 0):.0f}")


def plot_available_series(dataset: pd.DataFrame, x_column: str, y_columns: list[str], chart_type: str = "line") -> None:
    available_columns = [column for column in y_columns if column in dataset.columns]
    if not available_columns:
        st.info("No hay columnas disponibles para este grafico en el rango seleccionado.")
        return

    plot_frame = dataset[[x_column, *available_columns]].copy()
    plot_frame = plot_frame.dropna(how="all", subset=available_columns)
    if plot_frame.empty:
        st.info("No hay datos suficientes para este grafico en el rango seleccionado.")
        return

    if chart_type == "bar":
        figure = px.bar(plot_frame, x=x_column, y=available_columns, barmode="group")
    else:
        figure = px.line(plot_frame, x=x_column, y=available_columns)
    st.plotly_chart(figure, use_container_width=True)


def ensure_columns(dataset: pd.DataFrame, columns_with_defaults: dict[str, float]) -> pd.DataFrame:
    current = dataset.copy()
    for column, default_value in columns_with_defaults.items():
        if column not in current.columns:
            current[column] = default_value
        else:
            current[column] = current[column].fillna(default_value)
    return current


def is_metric_available(coverage_frame: pd.DataFrame, dataset_name: str) -> bool:
    match = coverage_frame[coverage_frame["dataset"] == dataset_name]
    if match.empty:
        return False
    return str(match.iloc[0]["status"]) != "missing"


def render_glossary(coverage_frame: pd.DataFrame) -> None:
    st.subheader("Glosario y criterio de interpretacion")
    st.write("Aqui diferenciamos entre datos Garmin reales, metricas derivadas locales y senales no disponibles hoy en tu cuenta.")
    rows = []
    for metric_key, metadata in METRIC_GLOSSARY.items():
        availability = metadata["type"]
        if metric_key == "readiness_score" and is_metric_available(coverage_frame, "training_readiness"):
            availability = "Garmin real"
        if metric_key == "training_status" and is_metric_available(coverage_frame, "training_status"):
            availability = "Garmin real"
        rows.append(
            {
                "metrica": metadata["label"],
                "tipo": availability,
                "significado": metadata["definition"],
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def render_metric_availability_notice(coverage_frame: pd.DataFrame) -> None:
    missing = coverage_frame[coverage_frame["status"] == "missing"]["dataset"].tolist()
    if missing:
        st.warning(
            "Estas senales no estan disponibles actualmente en tu cuenta o en esta ruta de ingesta: "
            + ", ".join(missing)
            + ". No deberian interpretarse como cero fisiologico."
        )


def main() -> None:
    st.title("Garmin Insights")
    st.caption("Plataforma local para recuperar, analizar y visualizar senales de entrenamiento y recuperacion.")

    (
        dataset,
        insight_frame,
        coverage_frame,
        manual_checkins,
        daily_summary_text,
        weekly_summary_text,
        best_days,
        worst_days,
        weekly_comparison,
        fatigue_alerts,
        weekly_narrative,
        best_day_narrative,
        worst_day_narrative,
        alerts_narrative,
    ) = load_dashboard_data()
    if dataset.empty:
        st.warning("No hay datos. Ejecuta primero los scripts de inicializacion e ingesta.")
        return

    dataset["metric_date"] = pd.to_datetime(dataset["metric_date"])
    min_date = dataset["metric_date"].min().date()
    max_date = dataset["metric_date"].max().date()

    start_date, end_date = st.sidebar.date_input(
        "Rango de fechas",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    filtered = dataset[(dataset["metric_date"].dt.date >= start_date) & (dataset["metric_date"].dt.date <= end_date)]
    filtered = ensure_columns(
        filtered,
        {
            "duration_hours": 0.0,
            "overnight_avg": 0.0,
            "resting_hr_bpm": 0.0,
            "readiness_score": 0.0,
            "body_battery_avg": 0.0,
            "total_training_load": 0.0,
            "activity_count": 0.0,
            "total_duration_minutes": 0.0,
            "weight_kg": 0.0,
            "body_fat_pct": 0.0,
            "muscle_mass_kg": 0.0,
            "body_water_pct": 0.0,
        },
    )

    render_metrics_row(filtered)
    render_metric_availability_notice(coverage_frame)
    st.info(daily_summary_text)
    st.caption(weekly_summary_text)

    tabs = st.tabs(
        [
            "Resumen general",
            "Sueno y recuperacion",
            "Entrenamiento y carga",
            "Tendencias",
            "Rendimiento y comparativos",
            "Check-ins manuales",
            "Glosario y semantica",
            "Peso y composicion corporal",
            "Cobertura de datos",
            "Insights automaticos",
        ]
    )

    with tabs[0]:
        st.subheader("Vista general")
        st.write("Interpretacion: esta vista resume las senales principales realmente disponibles hoy. Evitamos mezclar escalas incompatibles en un mismo grafico.")
        plot_available_series(filtered, "metric_date", ["duration_hours"])
        plot_available_series(filtered, "metric_date", ["overnight_avg", "resting_hr_bpm"])
        plot_available_series(filtered, "metric_date", ["total_training_load"], chart_type="bar")

    with tabs[1]:
        st.subheader("Sueno y recuperacion")
        st.write("Interpretacion: aqui si tiene sentido comparar sueno con HRV y resting HR, pero en paneles separados. Buscamos recuperacion incompleta, no coincidencias visuales artificiales.")
        plot_available_series(filtered, "metric_date", ["duration_hours", "sleep_hours_7d", "sleep_hours_28d"])
        plot_available_series(filtered, "metric_date", ["overnight_avg", "hrv_7d", "hrv_28d"])
        plot_available_series(filtered, "metric_date", ["resting_hr_bpm", "resting_hr_7d", "resting_hr_28d"])
        plot_available_series(filtered, "metric_date", ["body_battery_avg"])

        scatter_frame = filtered.copy()
        scatter_frame = scatter_frame.dropna(subset=["duration_hours", "overnight_avg"])
        if not scatter_frame.empty:
            st.write("Relacion exploratoria sueno vs HRV: util para detectar si peores noches coinciden con menor HRV respecto a tu propia base.")
            st.plotly_chart(
                px.scatter(scatter_frame, x="duration_hours", y="overnight_avg", color="metric_date"),
                use_container_width=True,
            )

    with tabs[2]:
        st.subheader("Entrenamiento y carga")
        st.write("Interpretacion: aqui analizamos carga y volumen. No mezclamos esta vista con sueno o HRV salvo en correlaciones concretas.")
        plot_available_series(filtered, "metric_date", ["activity_count", "total_duration_minutes", "total_training_load"], chart_type="bar")
        plot_available_series(filtered, "metric_date", ["acute_chronic_ratio"])

        load_recovery = filtered.copy()
        load_recovery = load_recovery.dropna(subset=["total_training_load", "overnight_avg"])
        if not load_recovery.empty:
            st.write("Relacion exploratoria carga diaria vs HRV: sirve para ver si cargas mas altas coinciden con descensos de recuperacion.")
            st.plotly_chart(
                px.scatter(load_recovery, x="total_training_load", y="overnight_avg", color="metric_date"),
                use_container_width=True,
            )

    with tabs[3]:
        st.subheader("Tendencias semanales y mensuales")
        st.write("Interpretacion: aqui comparamos promedios agregados por semana. Esta vista tiene mas sentido para tendencia que para detalle fisiologico fino.")
        trend = filtered.copy()
        trend["week"] = trend["metric_date"].dt.to_period("W").astype(str)
        weekly = trend.groupby("week", as_index=False).agg(
            avg_sleep=("duration_hours", "mean"),
            avg_hrv=("overnight_avg", "mean"),
            avg_rhr=("resting_hr_bpm", "mean"),
            total_load=("total_training_load", "sum"),
        )
        plot_available_series(weekly, "week", ["avg_sleep", "avg_hrv", "avg_rhr"])
        plot_available_series(weekly, "week", ["total_load"], chart_type="bar")

    with tabs[4]:
        st.subheader("Rendimiento y comparativos")
        st.write("Interpretacion: esta vista prioriza comparaciones accionables. Muestra que mejoro o empeoro esta semana y cuales fueron tus dias fisiologicamente mas fuertes o mas comprometidos.")
        st.info(weekly_narrative)
        if not weekly_comparison.empty:
            st.write("Comparacion semana reciente vs semana previa")
            st.dataframe(weekly_comparison, use_container_width=True)

        col_best, col_worst = st.columns(2)
        with col_best:
            st.write("Mejores dias recientes")
            st.caption(best_day_narrative)
            if best_days.empty:
                st.info("No hay datos suficientes para ranking de mejores dias.")
            else:
                st.dataframe(best_days, use_container_width=True)
        with col_worst:
            st.write("Dias con peor recuperacion potencial")
            st.caption(worst_day_narrative)
            if worst_days.empty:
                st.info("No hay datos suficientes para ranking de peores dias.")
            else:
                st.dataframe(worst_days, use_container_width=True)

        st.write("Alertas compuestas de fatiga")
        st.caption(alerts_narrative)
        if fatigue_alerts.empty:
            st.info("No hay alertas compuestas de fatiga en el periodo seleccionado.")
        else:
            fatigue_view = fatigue_alerts.copy()
            fatigue_view["metric_date"] = pd.to_datetime(fatigue_view["metric_date"])
            fatigue_view = fatigue_view[
                (fatigue_view["metric_date"].dt.date >= start_date) & (fatigue_view["metric_date"].dt.date <= end_date)
            ]
            st.dataframe(fatigue_view, use_container_width=True)

    with tabs[5]:
        st.subheader("Check-ins manuales")
        st.write("Registra contexto subjetivo para enriquecer la interpretacion mas alla de los sensores.")

        with st.form("manual_checkin_form", clear_on_submit=False):
            default_date = filtered["metric_date"].max().date()
            checkin_date = st.date_input("Fecha del check-in", value=default_date)
            col1, col2, col3 = st.columns(3)
            energy = col1.slider("Energia percibida", 1, 5, 3)
            stress = col2.slider("Estres laboral", 1, 5, 3)
            soreness = col3.slider("Dolor muscular", 1, 5, 3)
            col4, col5, col6 = st.columns(3)
            hydration = col4.slider("Hidratacion", 1, 5, 3)
            nutrition = col5.slider("Calidad de alimentacion", 1, 5, 3)
            mood = col6.slider("Estado emocional", 1, 5, 3)
            strength_load = st.slider("Carga de fuerza/gimnasio", 0, 5, 0)
            cycle_phase = st.text_input("Fase del ciclo menstrual (opcional)")
            notes = st.text_area("Notas")
            submitted = st.form_submit_button("Guardar check-in")

            if submitted:
                frame = pd.DataFrame(
                    [
                        {
                            "checkin_date": pd.to_datetime(checkin_date).strftime("%Y-%m-%d"),
                            "perceived_energy": energy,
                            "work_stress": stress,
                            "muscle_soreness": soreness,
                            "hydration": hydration,
                            "nutrition_quality": nutrition,
                            "mood": mood,
                            "strength_training_load": strength_load,
                            "menstrual_cycle_phase": cycle_phase or None,
                            "notes": notes or None,
                            "source": "manual_dashboard",
                        }
                    ]
                )
                DatabaseManager().upsert_dataframe("manual_checkins", frame, ["checkin_date"])
                st.cache_data.clear()
                st.success("Check-in guardado. Recarga la pagina si no ves el cambio de inmediato.")

        if manual_checkins.empty:
            st.info("Aun no hay check-ins manuales registrados.")
        else:
            st.dataframe(manual_checkins.sort_values("checkin_date", ascending=False), use_container_width=True)
            st.plotly_chart(
                px.line(
                    manual_checkins.sort_values("checkin_date"),
                    x="checkin_date",
                    y=["perceived_energy", "work_stress", "muscle_soreness", "hydration", "mood"],
                ),
                use_container_width=True,
            )

    with tabs[6]:
        render_glossary(coverage_frame)

    with tabs[7]:
        st.subheader("Peso y composicion corporal")
        st.write("Interpretacion: esta vista solo tiene sentido si realmente existe peso o composicion corporal en tu cuenta.")
        if is_metric_available(coverage_frame, "weight_body_composition"):
            plot_available_series(filtered, "metric_date", ["weight_kg"])
            plot_available_series(filtered, "metric_date", ["body_fat_pct", "muscle_mass_kg", "body_water_pct"])
        else:
            st.info("No hay datos reales de peso o composicion corporal disponibles actualmente.")

    with tabs[8]:
        st.subheader("Cobertura y calidad")
        st.write("Interpretacion: esta vista te dice con que datos reales contamos hoy, que tan completos estan y que falta para enriquecer el analisis.")
        if coverage_frame.empty:
            st.info("No hay reporte de cobertura disponible.")
        else:
            status_counts = coverage_frame.groupby("status", as_index=False).agg(total=("dataset", "count"))
            st.plotly_chart(px.bar(status_counts, x="status", y="total", color="status"), use_container_width=True)
            st.dataframe(
                coverage_frame[
                    [
                        "dataset",
                        "status",
                        "total_rows",
                        "first_date",
                        "last_date",
                        "populated_days",
                        "coverage_pct",
                        "available_columns",
                        "missing_columns",
                    ]
                ],
                use_container_width=True,
            )

    with tabs[9]:
        st.subheader("Insights automaticos")
        st.write("Cada insight incluye nombre, severidad, explicacion y recomendacion breve.")
        if insight_frame.empty:
            st.info("Aun no hay insights persistidos.")
        else:
            view = insight_frame.copy()
            if "insight_date" in view.columns:
                view["insight_date"] = pd.to_datetime(view["insight_date"])
                view = view[(view["insight_date"].dt.date >= start_date) & (view["insight_date"].dt.date <= end_date)]
            st.dataframe(
                view[["insight_date", "insight_name", "severity", "explanation", "recommendation"]].sort_values("insight_date", ascending=False),
                use_container_width=True,
            )


if __name__ == "__main__":
    main()

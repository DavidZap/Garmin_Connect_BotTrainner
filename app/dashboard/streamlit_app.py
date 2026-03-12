from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app.analytics import AnalyticsService
from app.insights import InsightService


st.set_page_config(page_title="Garmin Insights", layout="wide")


@st.cache_data
def load_dashboard_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    analytics = AnalyticsService()
    insights = InsightService(analytics=analytics)
    dataset = analytics.build_dashboard_dataset()
    insight_frame = analytics.db.read_sql("SELECT * FROM insights_history ORDER BY insight_date DESC")
    if insight_frame.empty:
        insight_frame = insights.generate_insights()
    return dataset, insight_frame


def render_metrics_row(dataset: pd.DataFrame) -> None:
    latest = dataset.sort_values("metric_date").iloc[-1]
    cols = st.columns(6)
    cols[0].metric("Sueno (h)", f"{latest.get('duration_hours', 0):.1f}")
    cols[1].metric("HRV", f"{latest.get('overnight_avg', 0):.1f}")
    cols[2].metric("Resting HR", f"{latest.get('resting_hr_bpm', 0):.1f}")
    cols[3].metric("Readiness", f"{latest.get('readiness_score', 0):.0f}")
    cols[4].metric("Pasos", f"{int(latest.get('steps', 0))}")
    cols[5].metric("Carga", f"{latest.get('total_training_load', 0):.0f}")


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


def main() -> None:
    st.title("Garmin Insights")
    st.caption("Plataforma local para recuperar, analizar y visualizar senales de entrenamiento y recuperacion.")

    dataset, insight_frame = load_dashboard_data()
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

    tabs = st.tabs(
        [
            "Resumen general",
            "Sueno y recuperacion",
            "Entrenamiento y carga",
            "Tendencias",
            "Peso y composicion corporal",
            "Insights automaticos",
        ]
    )

    with tabs[0]:
        st.subheader("Vista general")
        st.write("Interpretacion: revisa la relacion entre sueno, HRV, readiness y carga para ver equilibrio o fatiga.")
        plot_available_series(filtered, "metric_date", ["duration_hours", "overnight_avg", "resting_hr_bpm", "readiness_score"])
        plot_available_series(filtered, "metric_date", ["total_training_load"], chart_type="bar")

    with tabs[1]:
        st.subheader("Sueno y recuperacion")
        st.write("Interpretacion: caidas de HRV junto con subida de resting HR y poco sueno suelen sugerir recuperacion incompleta.")
        plot_available_series(filtered, "metric_date", ["duration_hours", "sleep_hours_7d", "sleep_hours_28d"])
        plot_available_series(filtered, "metric_date", ["overnight_avg", "hrv_7d", "resting_hr_bpm", "readiness_score", "body_battery_avg"])

    with tabs[2]:
        st.subheader("Entrenamiento y carga")
        st.write("Interpretacion: una subida rapida de la carga aguda frente a la cronica puede aumentar riesgo de fatiga.")
        plot_available_series(filtered, "metric_date", ["activity_count", "total_duration_minutes", "total_training_load"], chart_type="bar")
        plot_available_series(filtered, "metric_date", ["acute_chronic_ratio", "load_readiness_ratio"])

    with tabs[3]:
        st.subheader("Tendencias semanales y mensuales")
        st.write("Interpretacion: compara tus bases de 7 y 28 dias para detectar mejora, estabilidad o deterioro.")
        trend = filtered.copy()
        trend["week"] = trend["metric_date"].dt.to_period("W").astype(str)
        weekly = trend.groupby("week", as_index=False).agg(
            avg_sleep=("duration_hours", "mean"),
            avg_hrv=("overnight_avg", "mean"),
            avg_rhr=("resting_hr_bpm", "mean"),
            total_load=("total_training_load", "sum"),
            avg_readiness=("readiness_score", "mean"),
        )
        plot_available_series(weekly, "week", ["avg_sleep", "avg_hrv", "avg_rhr", "avg_readiness"])
        plot_available_series(weekly, "week", ["total_load"], chart_type="bar")

    with tabs[4]:
        st.subheader("Peso y composicion corporal")
        st.write("Interpretacion: cambios de peso deben leerse junto con carga, hidratacion y contexto de entrenamiento.")
        plot_available_series(filtered, "metric_date", ["weight_kg", "body_fat_pct", "muscle_mass_kg", "body_water_pct"])

    with tabs[5]:
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

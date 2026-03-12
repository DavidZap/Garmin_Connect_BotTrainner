# Importacion Real de Datos

La ruta recomendada en esta fase es cargar archivos CSV o JSON en `data/imports`.

## Archivos esperados

Puedes aportar uno o varios de estos archivos:

- `daily_summary.csv` o `.json`
- `sleep.csv` o `.json`
- `hrv.csv` o `.json`
- `resting_hr.csv` o `.json`
- `body_battery.csv` o `.json`
- `training_readiness.csv` o `.json`
- `training_status.csv` o `.json`
- `activities.csv` o `.json`
- `activity_details.csv` o `.json`
- `weight_body_composition.csv` o `.json`

## Reglas

- El nombre del archivo define el dataset.
- El importador acepta aliases comunes para columnas.
- Si faltan columnas opcionales, la carga sigue.
- Si faltan columnas requeridas, la carga falla con un mensaje claro.
- Si el dataset tiene fecha, se filtra por el rango pedido.

## Columnas minimas por dataset

- `daily_summary`: `summary_date`
- `sleep`: `sleep_date`
- `hrv`: `measurement_date`
- `resting_hr`: `measurement_date`
- `body_battery`: `measurement_date`
- `training_readiness`: `measurement_date`
- `training_status`: `measurement_date`
- `activities`: `activity_id`, `activity_date`
- `activity_details`: `activity_id`
- `weight_body_composition`: `measurement_date`

## Flujo en PowerShell

```powershell
Copy-Item .env.example .env -Force
python .\scripts\init_project.py
python .\scripts\import_real_data.py --days 3650
python .\scripts\run_dashboard.py
```

## Sugerencia practica

Empieza cargando solo estos cuatro datasets si aun no tienes todo:

- `activities`
- `sleep`
- `hrv`
- `resting_hr`

Con eso ya puedes empezar a responder preguntas reales de recuperacion, fatiga y relacion entre carga y descanso.

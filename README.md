# Garmin Insights

Sistema local-first en Windows para extraer, organizar, analizar y visualizar datos de Garmin Connect con Python, SQLite y Streamlit.

## 1. Resumen Ejecutivo

Este proyecto separa dos capas:

- Extraccion y automatizacion: obtiene datos Garmin, guarda crudos opcionalmente y persiste datos normalizados.
- Analisis e interpretacion: calcula metricas derivadas, genera insights y visualiza resultados.

La recomendacion es empezar con CLI para cargas reproducibles y dejar MCP como capa futura de orquestacion conversacional. SQLite permite avanzar rapido en local y la arquitectura deja preparada una migracion posterior a PostgreSQL.

## 2. Arquitectura Propuesta

### Capas

1. Extraccion y automatizacion
   - `app/config`
   - `app/ingestion`
   - `app/storage`
   - `scripts`

2. Analisis e interpretacion
   - `app/transformations`
   - `app/analytics`
   - `app/insights`
   - `app/dashboard`

### Flujo

1. Ingesta desde Garmin o archivos exportados.
2. Guardado opcional de crudos en `data/raw`.
3. Carga normalizada a SQLite.
4. Calculo de metricas derivadas.
5. Generacion de insights.
6. Visualizacion en Streamlit.

## 3. CLI vs MCP

### CLI

- Inicializacion
- Cargas historicas e incrementales
- Recalculo de metricas
- Exportes
- Dashboard

### MCP

- Consultas conversacionales
- Orquestacion con asistentes
- Integraciones futuras

### Recomendacion

Construir primero CLI. MCP debe venir despues sobre los mismos servicios Python.

## 4. Plan por Fases

### Fase 1

- Estructura de proyecto
- `.env`
- Logging
- SQLite
- Dashboard minimo

### Fase 2

- Adaptador real Garmin o importacion desde exportes
- Ingesta incremental
- Persistencia cruda
- Validacion ligera de archivos reales
- Soporte para Garmin CLI como fuente temporal

### Fase 3

- Modelo analitico
- Metricas derivadas
- Reglas de insights

### Fase 4

- Interpretacion deportiva
- Rankings y alertas
- Resumenes semanal y mensual

### Fase 5

- PostgreSQL
- Automatizacion programada
- MCP o API local

## 5. Estructura de Carpetas

```text
garmin_insights/
  app/
    analytics/
    config/
    dashboard/
    ingestion/
    insights/
    storage/
    transformations/
    utils/
  data/
    exports/
    processed/
    raw/
  docs/
  scripts/
  tests/
  .env.example
  requirements.txt
  README.md
```

## 6. Modelo de Datos

### `daily_summary`

- Proposito: estado diario consolidado.
- PK: `summary_date`
- Campos: pasos, calorias, distancia, pisos, minutos intensos.
- Granularidad: diaria.
- Relacion: eje temporal diario.

### `sleep`

- Proposito: calidad y cantidad de sueno.
- PK: `sleep_date`
- Campos: duracion, sleep score, fases, bedtime, wake_time.
- Granularidad: diaria.
- Relacion: cruza con readiness y carga.

### `hrv`

- Proposito: HRV diaria.
- PK: `measurement_date`
- Campos: promedio nocturno, baseline low/high, status.
- Granularidad: diaria.
- Relacion: cruza con RHR y fatiga.

### `resting_hr`

- Proposito: frecuencia cardiaca en reposo.
- PK: `measurement_date`
- Campos: `resting_hr_bpm`.
- Granularidad: diaria.
- Relacion: cruza con HRV.

### `body_battery`

- Proposito: energia corporal diaria.
- PK: `measurement_date`
- Campos: max, min, avg, fin del dia.
- Granularidad: diaria.

### `training_readiness`

- Proposito: readiness diario.
- PK: `measurement_date`
- Campos: score, nivel, factor limitante.
- Granularidad: diaria.

### `training_status`

- Proposito: estado de entrenamiento.
- PK: `measurement_date`
- Campos: status, load_ratio, VO2max, detalle.
- Granularidad: diaria.

### `activities`

- Proposito: catalogo de actividades.
- PK: `activity_id`
- Campos: fecha, deporte, duracion, distancia, FC, carga.
- Granularidad: actividad.
- Relacion: 1:N temporal hacia fechas; 1:1 con `activity_details`.

### `activity_details`

- Proposito: detalle de actividad.
- PK: `activity_id`
- Campos: elevacion, cadencia, potencia, training effect, JSON.
- Granularidad: actividad.

### `weight_body_composition`

- Proposito: peso y composicion corporal.
- PK: `measurement_date`
- Campos: peso, grasa, masa muscular, agua, BMI.
- Granularidad: diaria/evento.

### `derived_metrics`

- Proposito: metricas calculadas.
- PK: `metric_date`
- Campos: rolling means, variaciones, AC ratio, consistencia, streaks.
- Granularidad: diaria.

### `insights_history`

- Proposito: historial de insights.
- PK: `insight_id`
- Campos: fecha, nombre, severidad, explicacion, recomendacion, payload JSON.
- Granularidad: evento.

## 7. KPIs y Metricas Derivadas

### KPIs prioritarios

- Horas de sueno
- Sleep score
- HRV
- Resting HR
- Training readiness
- Body battery
- Pasos
- Intensidad de actividad
- Volumen semanal
- Duracion total de actividades
- Peso
- Tendencia de recuperacion
- Tendencia de fatiga

### Metricas derivadas

- Rolling mean 7 dias
- Rolling mean 28 dias
- Variacion diaria
- Variacion semanal
- Carga aguda vs cronica
- Consistencia del sueno
- Relacion HRV vs resting HR
- Relacion carga vs readiness
- Dias consecutivos de fatiga
- Dias consecutivos de buena recuperacion

## 8. Dashboard

Secciones:

1. Resumen general
2. Sueno y recuperacion
3. Entrenamiento y carga
4. Tendencias
5. Peso y composicion corporal
6. Insights automaticos

## 9. Datos disponibles, faltantes, limitaciones y supuestos

### Garmin razonablemente disponible

- Actividades
- Pasos y actividad diaria
- Sueno y sleep score en dispositivos compatibles
- HRV nocturna y HRV status en modelos compatibles
- Resting HR
- Body Battery
- Training Readiness
- Training Status
- Peso/composicion si hay Garmin Index o integracion

### Datos manuales recomendados

- Energia percibida
- Estres laboral
- Dolor muscular
- Alimentacion
- Hidratacion
- Ciclo menstrual
- Tipo de entrenamiento de fuerza
- Estado emocional

### Limitaciones

- No todos los dispositivos exponen lo mismo
- APIs no oficiales pueden cambiar
- Algunas metricas son propietarias
- Puede haber huecos historicos

### Supuestos

- SQLite al inicio
- Un solo usuario
- Fuente real Garmin se conecta despues
- Mientras tanto se soportan mocks o archivos en `data/imports`

## 10. Archivos

Cada archivo tiene una responsabilidad unica y clara dentro de la arquitectura modular.

## 11. Ejecucion en Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python .\scripts\init_project.py
python .\scripts\load_historical.py --days 180 --use-mock
python .\scripts\recalculate_metrics.py
python .\scripts\run_dashboard.py
```

Para importar archivos reales desde `data/imports`:

```powershell
python .\scripts\init_project.py
python .\scripts\import_real_data.py --days 3650
python .\scripts\run_dashboard.py
```

Para sincronizar datos recientes usando `garmin-connect` CLI:

```powershell
python .\scripts\sync_cli_data.py --days 30
python .\scripts\run_dashboard.py
```

Para sincronizar con la libreria Node `garmin-connect` usando el puente local:

```powershell
python .\scripts\sync_node_data.py --days 30
python .\scripts\run_dashboard.py
```

Para tomar todo el historial disponible via Node bridge:

```powershell
python .\scripts\backfill_node_data.py
python .\scripts\run_dashboard.py
```

Para exportar un resumen semanal narrativo:

```powershell
python .\scripts\export_weekly_report.py
```

Para registrar un check-in manual desde terminal:

```powershell
python .\scripts\add_manual_checkin.py --energy 4 --stress 2 --soreness 3 --hydration 4 --nutrition 4 --mood 4 --notes "Me senti bien"
```

## 12. Proximos Pasos Priorizados

1. Conectar Garmin real o export oficial.
2. Agregar datos subjetivos/manuales.
3. Mejorar correlaciones y alertas.
4. Preparar PostgreSQL.
5. Exponer servicios para CLI enriquecido o MCP.

# Ingesta con Node Bridge y `garmin-connect`

Esta es la ruta recomendada temporal mientras llega tu export oficial de Garmin.

## Idea

- Python sigue siendo el orquestador principal.
- Node solo se usa como puente hacia la libreria `garmin-connect`.
- Los datos terminan igual en SQLite y en el dashboard Streamlit.

## Requisitos

1. Tener Node.js instalado.
2. Tener la libreria `garmin-connect` instalada global o localmente.
3. Definir credenciales Garmin en `.env`.

## Variables necesarias

```powershell
GARMIN_SOURCE=node
GARMIN_NODE_COMMAND=node
GARMIN_USERNAME=tu_correo
GARMIN_PASSWORD=tu_password
```

## Ejecucion

```powershell
.\.venv\Scripts\Activate.ps1
python .\scripts\init_project.py
python .\scripts\sync_node_data.py --days 30
python .\scripts\run_dashboard.py
```

## Cobertura actual

- Actividades
- Detalle basico de actividades
- Pasos
- Sueno
- HRV nocturna derivada de `getSleepData`
- Resting HR
- Body Battery nocturna disponible en `sleepBodyBattery`
- Peso y composicion corporal si existen en la cuenta

## Limitaciones actuales

- No cubre aun `training_readiness` ni `training_status`
- Body Battery no es intradia completo, solo lo disponible en el payload de sueno
- Depende de que la libreria pueda autenticarse correctamente en tu cuenta

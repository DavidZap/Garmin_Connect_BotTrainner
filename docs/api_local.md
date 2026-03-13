# API Local con FastAPI

Esta API expone el nucleo analitico local para preparar futuras integraciones como PWA Android o MCP.

## Arranque

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\scripts\run_api.py
```

## URL base

```text
http://127.0.0.1:8000
```

## Documentacion interactiva

```text
http://127.0.0.1:8000/docs
```

## Endpoints principales

- `GET /health`
- `GET /coverage`
- `GET /daily`
- `GET /insights`
- `GET /performance/weekly-comparison`
- `GET /performance/best-days`
- `GET /performance/worst-days`
- `GET /performance/fatigue-alerts`
- `GET /narrative/weekly`
- `GET /narrative/best-day`
- `GET /narrative/worst-day`
- `GET /manual-checkins`
- `POST /manual-checkins`
- `GET /meta/summary`

## Uso futuro

Esta API sera la base recomendada para:

- frontend PWA instalable en Android
- capa MCP
- integraciones externas

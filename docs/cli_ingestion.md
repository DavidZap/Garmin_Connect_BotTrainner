# Ingesta con Garmin Connect CLI

Este proyecto ya soporta `GARMIN_SOURCE=cli` para extraer datos usando el CLI de Garmin Connect como fuente incremental.

## Referencias usadas

- MCP de referencia: [DavidZap/garmin-connect-mcp](https://github.com/DavidZap/garmin-connect-mcp)
- CLI de referencia: [eddmann/garmin-connect-cli](https://skills.sh/eddmann/garmin-connect-cli/garmin-connect)

## Para que sirve aqui

- Obtener datos recientes mientras llega el export oficial.
- Poblar SQLite sin depender de archivos manuales.
- Mantener una ruta incremental local-first.

## Recomendacion

Usa CLI para ventanas recientes, por ejemplo 7 a 30 dias. Para historico amplio, sigue siendo mejor el export oficial.

## Instalacion sugerida en Windows

1. Instala Node.js.
2. Instala o expone el binario `garmin-connect`.
3. Verifica:

```powershell
garmin-connect auth status
```

Si el binario queda con otro nombre o ruta, configuralo en `.env`:

```powershell
GARMIN_SOURCE=cli
GARMIN_CLI_COMMAND=garmin-connect
```

## Ejecucion

```powershell
.\.venv\Scripts\Activate.ps1
python .\scripts\init_project.py
python .\scripts\sync_cli_data.py --days 30
python .\scripts\run_dashboard.py
```

## Cobertura actual del adaptador

- `activities list`
- `activities get <id> --details`
- `health steps --date`
- `health sleep --date`
- `health rhr --date`
- `health body-battery --date`
- `training readiness --date`
- `training status --date`
- `training hrv --date`
- `weight list --start --end`

## Nota

Los nombres exactos de campos devueltos por el CLI pueden variar. El adaptador actual usa parseo tolerante con aliases y best effort.

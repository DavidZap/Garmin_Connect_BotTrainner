# Automatizacion Diaria en Windows

La forma mas simple de automatizar hoy este proyecto es programar `daily_refresh.py` con el Programador de tareas de Windows.

## Comando recomendado

```powershell
.\.venv\Scripts\python.exe .\scripts\daily_refresh.py --days 7 --source node
```

## Que hace

- sincroniza datos recientes desde Garmin
- recalcula metricas derivadas
- regenera insights
- exporta un resumen semanal narrativo en `data/exports/weekly_report_latest.md`

## Programador de tareas

1. Abrir `Task Scheduler`
2. Crear tarea basica
3. Elegir frecuencia diaria
4. Accion: `Start a program`
5. Programa:

```text
C:\Users\David\Documents\Ejemplos Codex\Projecto Garmin Connect\.venv\Scripts\python.exe
```

6. Argumentos:

```text
.\scripts\daily_refresh.py --days 7 --source node
```

7. Iniciar en:

```text
C:\Users\David\Documents\Ejemplos Codex\Projecto Garmin Connect
```

## Recomendacion

Ejecutarlo una vez al dia temprano en la manana, despues de que Garmin ya haya sincronizado el reloj.

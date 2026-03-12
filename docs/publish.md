# Publicacion en GitHub

Este proyecto debe publicarse sin secretos ni datos locales.

## No subir

- `.env`
- `data/raw`
- `data/processed`
- `data/exports`
- `data/imports`
- `.venv`

## Flujo recomendado

```powershell
git init
git branch -M main
git remote add origin https://github.com/DavidZap/Garmin_Connect_BotTrainner.git
git add .
git status
git commit -m "Initial Garmin Insights project"
git push -u origin main
```

## Antes del push

- Verifica que `.env` no este staged.
- Verifica que la base SQLite no este staged.
- Verifica que no haya JSON crudos de Garmin staged.


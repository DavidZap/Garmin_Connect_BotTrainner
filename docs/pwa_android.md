# PWA Android

Esta fase agrega una PWA minima viable servida desde FastAPI.

## Arranque local

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\scripts\run_api.py
```

Luego abre:

```text
http://127.0.0.1:8000
```

## Instalacion en Android

1. Abre la URL en Chrome para Android.
2. En el menu del navegador elige `Agregar a pantalla principal` o `Instalar aplicacion`.
3. La app quedara con icono propio y modo standalone.

## Que incluye esta primera PWA

- resumen diario
- narrativa semanal
- comparacion semanal
- mejores y peores dias
- alertas de fatiga
- formulario de check-in manual

## Limite actual

Esta primera version esta pensada para correr sobre tu API local. Para usarla desde el celular fuera del PC, el siguiente paso sera definir despliegue local en red o un backend hospedado.

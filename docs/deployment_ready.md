# Deployment Ready

Esta fase deja el proyecto listo para desplegar API + PWA fuera de tu PC.

## Cambios clave

- configuracion de host y puerto por entorno
- soporte explicito para PostgreSQL via `psycopg`
- `Dockerfile`
- `.dockerignore`
- `render.yaml`

## Arranque local con acceso desde otros dispositivos de tu red

En `.env`:

```dotenv
APP_HOST=0.0.0.0
APP_PORT=8000
PUBLIC_BASE_URL=http://TU_IP_LOCAL:8000
```

Luego:

```powershell
python .\scripts\run_api.py
```

## Despliegue recomendado

### Etapa 1

- Render o Railway
- PostgreSQL administrado
- secretos como variables de entorno

### Etapa 2

- VPS propio si quieres mas control
- jobs programados para `daily_refresh.py`
- dominio y HTTPS

## Estrategia recomendada de credenciales Garmin

No recomiendo pedir usuario y password Garmin en cada apertura de la app.

Recomendacion:

1. Primera configuracion u onboarding
2. Guardar credenciales o tokens de forma segura en backend, no en el navegador
3. En cloud, usar secretos del proveedor
4. En futuro, sustituir password por tokens o sesion reutilizable cuando sea posible

## Nota importante

Si tus credenciales Garmin llegaron a quedar visibles en archivos versionados o compartidos, cambialas cuanto antes.


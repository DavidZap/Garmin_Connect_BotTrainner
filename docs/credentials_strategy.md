# Estrategia de Credenciales

## Preguntar credenciales al inicio de la app

Se puede, pero no es la mejor experiencia ni la mejor seguridad si se hace en cada apertura.

## Mejor enfoque

- pedir credenciales una sola vez en onboarding
- enviarlas por HTTPS al backend
- guardarlas como secreto de backend o convertirlas en tokens reutilizables
- no almacenarlas en `localStorage`
- no exponerlas en el frontend PWA

## Recomendacion por etapa

### Ahora

- usar `.env` o secretos del proveedor cloud
- no pedirlas desde la PWA todavia
- si despliegas en Render/Railway, guardarlas como variables secretas del servicio

### Despues

- crear una pantalla de onboarding protegida
- backend guarda secreto cifrado o token de sesion
- la PWA solo dispara `refresh`, nunca gestiona password directamente

## Recomendacion concreta para este proyecto

Hoy conviene:

1. desplegar primero con secretos de backend
2. validar estabilidad de sincronizacion Garmin en cloud
3. solo despues evaluar onboarding de credenciales desde la app

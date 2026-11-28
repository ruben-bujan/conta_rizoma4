# Manual de usuario — conta-rizoma4

## Acceso
- API: http://localhost:8001 (configurable CONTA_API_URL)
- CLI: `conta` (tras `pip install -e .`)

## Flujo de asiento (Fase 4)
1. Admin reserva lease para operario → POST /leases
2. Operario crea asiento → POST /asientos → BORRADOR
3. Jefe de obra visa → POST /asientos/{id}/visar → VISADO
4. Jefe de producción aprueba → POST /asientos/{id}/aprobar → APROBADO
5. Admin registra resultado de rizomización → POST /asientos/{id}/rizomizar → RIZOMIZADO o EN_CUARENTENA

## Configuración de usuario
Variables: CONTA_API_URL, CONTA_HTTP_URL, CONTA_DEMO_OK, CONTA_SINTETICO_OK.

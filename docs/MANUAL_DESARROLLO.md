# Manual de desarrollo — conta-rizoma4

## 1. Arquitectura
- Hijo (conta-rizoma4): contabilidad PGC español, API FastAPI, CLI
- Padre (rizoma4): kernel epistémico, integración HTTP + parsers.contrato_dominio

## 2. Instalación
Ver README.md sección Instalación. Requiere MariaDB + PostgreSQL.

## 3. Configuración
Copia `config/conta_config.json.example` → `config/conta_config.json`.
Bloques: `admin` (infra/credenciales/JWT/API/RIZOMA4) y `user` (runtime).
Visado del superior controla cambios sensibles.

## 4. Variables personalizables
Ver listado en README/config. ADMIN: MARIADB_*, CONTA_PG_*, CONTA_JWT_SECRET, CONTA_API_*, RIZOMA4_*, CONTA_RIZOMA4_PATH, CONTA_BACKEND, CONTA_CACHE_DIR, CONTA_EMPRESAS_YAML, CONTA_ENV.
USER: CONTA_API_URL, CONTA_HTTP_URL, CONTA_DEMO_OK, CONTA_SINTETICO_OK.

## 5. Estructura de código
- conta_rizoma4/api/ — FastAPI routers
- conta_rizoma4/partida_doble/ — libros contables
- conta_rizoma4/operativo/ — actos económicos
- conta_rizoma4/contratos/ — contratos de dominio
- conta_rizoma4/corpus_forense/ — corpus forense
- conta_rizoma4/custodia/ — custodia
- conta_rizoma4/consolidacion/ — consolidación

## 6. Tests
`pytest -m 'not integration and not slow'`. Tests de integración requieren servicios reales.

## 7. Integración con rizoma4
Cliente HTTP: `conta_rizoma4/api/rizoma4_client.py`. Import Python: `parsers.contrato_dominio`.

## 8. Gobernanza
matriz_competencias.md, actas en gobernanza/.

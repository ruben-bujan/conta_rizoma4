# Núcleo formal del dominio epistemológico-contable

## Estado

Este paquete contiene una promoción parcial del dominio y un ledger/event store
en memoria. **VERIFICADO 2026-11-26:** los eventos incluyen estado anterior y
posterior cubierto por hash encadenado, `verificar_cadena` detecta manipulación y
`reconstruir` recupera 14 tipos de proyección (entidades, actores, fuentes,
hechos, evidencias, valoraciones de evidencia, criterios, autorizaciones,
interpretaciones, decisiones, representaciones, rectificaciones, ejercicios y
cierres). Hay autorizaciones con vigencia/revocación, roles, jerarquía, permisos,
`verificar_competencia`, modo contable, avocación/inhibición/visado, intervención
ADMIN, criticidad de importe y registros sin asiento. 138 pruebas de
dominio/adaptadores/API simulada pasaron en la revisión.

**VERIFICADO 2026-11-26:** la reconstrucción cubre los tipos de evento de
autoridad y `verificar_competencia` está conectada a decisiones,
representaciones, asientos diarios, rectificaciones, cierres y reaperturas
según `gobernanza/matriz_competencias.md`, aprobada por
`gobernanza/acta_aprobacion_matriz_competencias.md`.

**VERIFICADO 2026-11-26:** la API expone `actor_id` y mapea sus roles a `Actor`
de dominio (`conta_rizoma4/api/deps.py`). La presencia de estos controles no
acredita por sí sola autoridad profesional suficiente; queda verificar permisos
expresos y segmentación por empresa en un entorno aislado con PostgreSQL.

Incluye adaptador de memoria, adaptador PostgreSQL de solo lectura y un
importador de correspondencias heredadas que puede escribir correspondencias
cuando se invoca expresamente. No incluye un repositorio PostgreSQL productivo
completo para todas las entidades del dominio.

La API heredada, su autenticación HTTP, el CAS externo y la integración directa
con RIZOMA4 se mantienen fuera del núcleo puro. Los casos de uso y la
presentación normativa siguen parciales: la presentación PGC-PYMES genera
trazabilidad de reglas pero sus reglas base no tienen fuente normativa ni
revisión aprobada, y el fiscal dispone de reglas inmutables/versionadas sin
catálogo oficial.

## Estructura

- `entidades/economicas.py`: hechos, partes, fechas e incertidumbre.
- `entidades/epistemicas.py`: fuentes, evidencias, criterios e interpretaciones.
- `entidades/contables.py`: decisiones, autorizaciones, asientos, rectificaciones y eventos, con roles y jerarquía de autoridad.
- `servicios/nucleo.py`: event store, verificación de cadena, reconstrucción y controles de autoridad.
- `casos_uso/`: cierre, conciliación, facturación, existencias e inmovilizado sobre el núcleo.
- `presentacion/`: reglas de presentación con vigencia/revisión y paquete PGC-PYMES no apto para depósito.
- `fiscal/`: reglas fiscales inmutables/versionadas y modelos 200/303 analíticos.
- `puertos/repositorio.py`: contrato abstracto de repositorio.
- `adaptadores/repositorio_memoria.py`: adaptador de memoria.
- `adaptadores/postgresql_lectura.py`: lectura explícitamente de solo lectura.
- `adaptadores/repositorio_postgres.py`: importador limitado de correspondencias heredadas.
- `compatibilidad_poc.py`: adaptador temporal con la POC.

## Regla arquitectónica

El núcleo puro no puede importar:

- psycopg;
- FastAPI;
- requests;
- JWT;
- Rizoma4;
- un repositorio PostgreSQL;
- una API HTTP.

## Compatibilidad

Los adaptadores de infraestructura permanecen en `adaptadores/`; no deben
importarse desde entidades ni servicios puros. La POC puede utilizarse
temporalmente como:

- laboratorio de casos;
- referencia de escenarios;
- generador de datos de prueba;
- adaptador hacia el dominio formal.

No debe convertirse en dependencia permanente del paquete formal.

## Próximo incremento

1. verificar los permisos expresos y la segmentación por empresa en un entorno aislado con PostgreSQL;
2. completar reglas PGC-PYMES con fuente normativa, vigencia y revisión identificadas y catálogo fiscal oficial;
3. verificar correspondencias heredadas y rollback en un entorno aislado;
4. diferir la escritura PostgreSQL completa y la integración RIZOMA4 hasta sus hitos aprobados.

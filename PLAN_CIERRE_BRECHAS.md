# Programa de cierre de brechas de CONTA-RIZOMA4

## Propósito

Cerrar de forma demostrable las carencias descritas en el dictamen del estado del proyecto para avanzar hacia una herramienta integral de contabilidad e investigación económica, con **máxima seguridad jurídica**.

Este documento es un programa de trabajo, no una afirmación de cumplimiento ni una aprobación de criterios contables o jurídicos. No autoriza por sí mismo escrituras, migraciones, despliegues ni cambios en datos reales.

## Reglas de ejecución

1. Mantener el orden vigente: fases 2, 3, 4, 5 y 7; después las fases 1 y 6, que permanecen en `COLA_ESPERA_2.md` hasta instrucción expresa.
2. Trabajar primero con dominio puro y repositorio en memoria. PostgreSQL y otros adaptadores se validan después en un entorno aislado.
3. No promover una salida analítica a declaración, asiento aprobado o cumplimiento formal sin revisión y autoridad identificadas.
4. Cada incremento conserva historial, separa hecho/evidencia/interpretación/decisión/representación y distingue fechas económica, de conocimiento y de registro.
5. Clasificar hallazgos y resultados como **VERIFICADO**, **DOCUMENTADO**, **INFERIDO**, **PROPUESTA** o **NO DETERMINADO**.
6. No ejecutar DDL, migraciones ni escrituras sobre datos reales durante los incrementos de dominio. La activación de producción es un hito separado y requiere aprobaciones técnicas, contables y jurídicas.

## Revisión de código 2026-11-26

Revisión directa de `conta_rizoma4/dominio/`, pruebas y API. No activa fases, no aprueba matrices de competencias y no sustituye las decisiones pendientes.

| Tramo | Estado real | Evidencia |
|---|---|---|
| 0 — Base verificable y segura | **PARCIAL** | CORS por lista explícita (`conta_rizoma4/api/main.py:42-53`), JWT sin secreto por defecto y alta inicial de administrador documentada (`conta_rizoma4/api/AUTH.md:5-23`), corpus forense restringido a `admin` (`conta_rizoma4/api/routers/corpus_forense.py:27`), límite de 20 MiB en documentos (`conta_rizoma4/api/routers/documentos.py:16`). Sin matriz completa de permisos por ruta, sin limitación de intentos de login y sin verificación de instalación limpia/despliegue. |
| 1 — Reconstrucción y auto-verificación | **IMPLEMENTADO EN MEMORIA; PARCIAL** | Eventos con estado anterior/posterior y hash encadenado (`conta_rizoma4/dominio/servicios/nucleo.py:109-158`), `verificar_cadena` (`:1109-1135`) y `reconstruir` (`:1137-1268`) sobre 14 tipos: entidades, actores, fuentes, hechos, evidencias, valoraciones de evidencia, criterios, autorizaciones, interpretaciones, decisiones, representaciones, rectificaciones, ejercicios y cierres. 17 pruebas en `tests/test_nucleo_dominio.py` y 5 en `tests/test_escenarios_dominio.py`. La reconstrucción aún no cubre los 8 tipos nuevos de autoridad: permisos, solicitudes/informes/remisiones ADMIN, alertas, registros sin asiento, modos y calificaciones de entidad. |
| 2 — Competencias y límites de autoridad | **PARCIAL** | Roles y jerarquía (`conta_rizoma4/dominio/entidades/contables.py:10-17`, `:55-62`), `autorizacion_id` obligatorio en decisión y representación (`:103-109`, `:135-141`), autorización con alcance en decisiones y cierre (`conta_rizoma4/dominio/servicios/nucleo.py:513-546`, `:180-267`), permisos y `verificar_competencia` (`:676-766`), reglas de modo, avocación/inhibición/visado e intervención ADMIN (`:782-1010`) y umbrales de criticidad (`:1043-1069`). La matriz está aprobada (`gobernanza/acta_aprobacion_matriz_competencias.md`), `verificar_competencia` se invoca en las operaciones principales del núcleo y la API mapea la identidad autenticada a `Actor` (`conta_rizoma4/api/deps.py`). |
| 3 — Formulación PGC-PYMES | **PARCIAL** | `ReglaPresentacion` con fuente, vigencia y revisión (`conta_rizoma4/dominio/presentacion/presentacion.py:15-45`), `presentar_pymes` con trazabilidad de reglas y pendientes explícitos (`conta_rizoma4/dominio/presentacion/pymes.py:29-120`), 7 pruebas en `tests/test_presentacion_pymes.py`. Las reglas base conservan `referencia_normativa=None` y `revisada_por=None` (`presentacion.py:65-119`), por lo que el paquete sigue sin ser formulable ni apto para depósito. |
| 4 — Cierre integral | **PARCIAL** | `conta_rizoma4/dominio/casos_uso/cierre.py` produce la hoja de trabajo de los grupos 1-7 y delega el registro en el núcleo con actor/autorización (`nucleo.py:180-267`); 8 pruebas en `tests/test_casos_uso_cierre.py`. Siguen sin integrarse como precondición vencimientos, conciliaciones, periodificaciones, amortizaciones y deterioros; no hay bloqueo/concurrencia reales y las líneas propuestas no se contabilizan solas. |
| 5 — Conciliación bancaria | **PARCIAL** | `conta_rizoma4/dominio/casos_uso/conciliacion.py` propone vínculos 1:1 y deja las diferencias como pendientes; 6 pruebas en `tests/test_conciliacion_dominio.py`. Falta importación de extractos, idempotencia por origen, comisiones, fechas de valor, transferencias internas y autorización en la representación. |
| 6 — Correcciones y facturación | **PARCIAL** | `conta_rizoma4/dominio/casos_uso/facturacion.py` exige `autorizacion_id` y `rectificaciones.py` separa la rectificativa. Las 12 pruebas heredadas de casos de uso ya pasan `autorizacion_id` sin debilitar la autorización. Numeración, no reutilización y no supresión quedan fuera del caso de uso. |
| 7 — Modelos fiscales | **PARCIAL** | Regla fiscal inmutable y vigente por fecha de conocimiento (`conta_rizoma4/dominio/fiscal/versionado.py`), modelos 200/303 analíticos y versionados (`conta_rizoma4/dominio/fiscal/modelos.py`), 10 pruebas en `tests/test_fiscal_dominio.py`. No hay catálogo oficial, reglas de elegibilidad ni declaración en formato AEAT. |
| 10 — PostgreSQL y migración externa | **PARCIAL** | Adaptador de lectura, verificación dual y `migrations/006` con guardas append-only/rollback documentados. El expediente INCIVSA acredita importación en `BORRADOR` en entorno aislado, con 31 pruebas referidas en `pilot_incivsa/informe_migracion_2026-11-25.md`. No se ensayó restauración completa; falta la escritura PostgreSQL completa del dominio y la activación. |
| 11 — Seguridad operativa y aislamiento | **PARCIAL** | Sin comodín CORS, sin secreto JWT por defecto, corpus admin-only y límite de 20 MiB; siguen pendientes el limitador de login, límites globales de petición y el acta de seguridad. Aislamiento multi-empresa de la API heredada: **NO DETERMINADO**. |

Evidencia de ejecución de esta revisión:

- suite amplia de dominio/adaptadores/API simulada: **138 passed in 2.05s**;
- suite de actos avanzados: **57 passed in 0.72s**;
- suite completa anterior con `CONTA_PG_URL=postgresql://test:test@localhost:5432/test`: **47 failed, 392 passed, 5 skipped, 1 warning, 91 errors in 6.09s**. Causas: PostgreSQL sin rol `test`, falta `config/empresas.yaml` y 12 fallos reales por firma con `autorizacion_id`.
- tras P0, sin variables PostgreSQL: **353 passed, 182 deselected, 1 warning in 2.86s**; las 182 pruebas de integración se recogen con `pytest -m integration --collect-only -q`. En ese momento PostgreSQL no tenía rol `test`; la ejecución real posterior figura en la evidencia de P1.

## Ruta a producción: funcionalidades y archivos

Convierte los tramos anteriores en entregables verificables con archivos concretos. **No autoriza** DDL, migraciones, despliegues, activación de datos reales ni aprobación de asientos o declaraciones. Cada puerta se cierra con evidencia; las que deciden criterio contable, fiscal o jurídico exigen además un acta humana identificada. Sin esa acta, el resultado permanece `NO DETERMINADO`.

### P0 — Base reproducible y suite verde — **CERRADA**

- **Funcionalidad:** arranque y pruebas reproducibles sin depender de secretos ni de una base accidental; separación clara entre pruebas unitarias y de integración.
- **Modificar:** `conta_rizoma4/config/empresas.py` (documenta `CONTA_EMPRESAS_YAML`), `tests/test_casos_uso_existencias.py`, `tests/test_casos_uso_facturacion.py`, `tests/test_casos_uso_inmovilizado.py`, `tests/test_casos_uso_tesoreria.py` (pasan `autorizacion_id` sin debilitar la autorización), `.gitignore` (ignora `config/empresas.yaml`).
- **Incorporar:** `config/empresas.yaml` local desde `config/empresas.yaml.example` sin secretos ni datos reales, `Makefile` que incluye `.makefile`, `tests/conftest.py` que marca como `integration` los módulos con acceso a PostgreSQL y fija una URL de prueba sintética para la importación de módulos. `tests/test_conftest.py` queda inactivo como fixture global: no se usa y sigue marcado como integración.
- **Evidencia de cierre:** `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/ruben/MyProyecto/rizoma4:/home/ruben/MyProyecto/conta-rizoma4 .venv/bin/python -m pytest -q` terminó con **353 passed, 182 deselected, 1 warning in 2.86s**. `make -n test` muestra `pytest -m "not integration and not slow"`. `pytest -m integration --collect-only -q` recoge 182 pruebas. La ejecución real de integración se realizó después contra un PostgreSQL aislado con rol `test`; ver la evidencia de P1. La instalación desde cero con el checkout local de `rizoma4` sigue documentada en la sección de instalación de `README.md`.

### P1 — Autoridad aplicada y reconstrucción completa

- **Funcionalidad:** toda decisión, representación, rectificación, cierre y reapertura comprueba competencia y alcance; la identidad autenticada de la API se convierte en `Actor` de dominio; el ledger reconstruye también los 8 tipos de evento de autoridad.
- **Modificar:** `conta_rizoma4/dominio/servicios/nucleo.py` (invocar `verificar_competencia` en `adoptar_decision`, `crear_representacion`, `crear_rectificacion`, `registrar_cierre_ejercicio` y `registrar_reapertura_ejercicio`; ampliar `reconstruir`), `conta_rizoma4/dominio/entidades/contables.py` (sólo si faltan competencias), `conta_rizoma4/dominio/adaptadores/repositorio_memoria.py`, `conta_rizoma4/auth.py` (exigir `CONTA_JWT_SECRET` siempre en producción y exponer `actor_id`/rol), `conta_rizoma4/api/routers/asientos.py`, `empresas.py`, `leases.py`, `obras.py`, `operarios.py`, `documentos.py` y `corpus_forense.py`, `tests/test_nucleo_dominio.py`, `tests/test_api_seguridad_auth.py`, `tests/test_escenarios_dominio.py`.
- **Incorporar:** `conta_rizoma4/api/deps.py` (dependencia única de actor/permiso) y `gobernanza/matriz_competencias.md` con responsable, alcance, vigencia y aprobación.
- **Evidencia de cierre:** pruebas de rechazo por falta de competencia en cada operación, reconstrucción de los 22 tipos de evento y acta firmada de la matriz.
- **Avance parcial 2026-11-26:** `reconstruir` ya proyecta permisos, modos, avocación, inhibición, visado, solicitudes/informes/remisión ADMIN y registros sin asiento. La matriz quedó aprobada por el responsable en `gobernanza/acta_aprobacion_matriz_competencias.md`; `verificar_competencia` está enlazada a decisiones, representaciones, asientos, rectificaciones, cierres y reaperturas, con pruebas de rechazo por rol. Suite segura tras la ronda de roles: `371 passed, 185 deselected, 1 warning in 2.81s`. Suite `integration` contra PostgreSQL efímero con DDL/migraciones aisladas, datos PGC sintéticos y sin el trigger de mantenimiento de `004_inmutabilidad.sql`: `185 passed, 371 deselected, 1 warning in 13.32s`. **VERIFICADO:** la API expone `actor_id` en el token y mapea `aux_obra`→`AUXILIAR`, `visador`→`JEFE_CONTABILIDAD`, `aprobador`→`SUBDIRECTOR` y `admin`→`ADMIN` en `conta_rizoma4/api/deps.py`. `aux_obra` no puede registrar asientos en el núcleo por el umbral de `ASIENTO_DIARIO` salvo delegación vigente en `dominio_evento`; ese cable HTTP y su prueba ya están implementados.

### P2 — Catálogos PGC-PYMES y fiscal con fuente aprobada

- **Funcionalidad:** reglas de presentación y fiscales cargadas desde catálogos versionados con fuente normativa, vigencia por fecha de conocimiento y revisor identificable; suficiencia y clasificación del ECPN antes de cualquier formulación.
- **Modificar:** `conta_rizoma4/dominio/presentacion/presentacion.py`, `conta_rizoma4/dominio/presentacion/pymes.py`, `conta_rizoma4/dominio/fiscal/versionado.py`, `conta_rizoma4/dominio/fiscal/modelos.py`, `conta_rizoma4/cuentas_anuales_oficiales/memoria.py`, `tests/test_presentacion_pymes.py`, `tests/test_fiscal_dominio.py`.
- **Incorporar:** `gobernanza/catalogo_pgc_pymes.yaml` y `gobernanza/catalogo_fiscal.yaml` como datos versionados; no incorporar formatos AEAT/Registro Mercantil sin decisión separada.
- **Evidencia de cierre:** `apta_para_deposito` sólo cambia con reglas revisadas; cobertura íntegra por modelo/partida y memorias justificadas con responsable.

### P3 — Cierre, conciliación y correcciones enlazadas

- **Funcionalidad:** el cierre exige vencimientos, conciliaciones, periodificaciones, amortizaciones y deterioros resueltos; conciliación con origen idempotente y diferencias autorizadas; numeración/no reutilización de facturas fuera del caso de uso pero verificada en el adaptador.
- **Modificar:** `conta_rizoma4/dominio/casos_uso/cierre.py`, `conciliacion.py`, `facturacion.py`, `rectificaciones.py`, `tesoreria.py`, `inmovilizado.py`, `existencias.py`, `conta_rizoma4/dominio/servicios/vencimientos.py`, `libros.py`, `conta_rizoma4/dominio/servicios/nucleo.py` y las pruebas `tests/test_casos_uso_*.py`, `tests/test_conciliacion_dominio.py`, `tests/test_vencimientos_dominio.py`, `tests/test_libros_dominio.py`.
- **Incorporar:** `gobernanza/politicas_valoracion.yaml` si la política de valoración/amortización debe quedar ligada a entidad y ejercicio.
- **Evidencia de cierre:** hoja de cierre con precondiciones fallidas explícitas; líneas propuestas nunca se confunden con asientos aprobados.

### P4 — Persistencia PostgreSQL de producción

- **Funcionalidad:** repositorio append-only real, transacciones todo-o-nada, verificación dual y procedimiento de migración reversible. La activación sigue siendo un hito posterior.
- **Modificar:** `conta_rizoma4/dominio/adaptadores/postgresql_escritura_diseno.py` (contrato), `conta_rizoma4/dominio/adaptadores/postgresql_lectura.py`, `conta_rizoma4/dominio/verificacion_migracion.py`, `conta_rizoma4/config/postgresql.py`, `scripts/migrate.py` (dry-run, checksum, guarda de entorno y una transacción por migración), `migrations/005_dominio_epistemico.sql` y `migrations/006_incivsa_importacion.sql` (revisión; el aviso "NO EJECUTAR" se retira sólo tras ensayo de rollback), `tests/test_postgresql_escritura_diseno.py`, `tests/test_migracion_integrada.py`, `tests/test_verificacion_migracion.py`, `pilot_incivsa/test_migracion_segura.py`.
- **Incorporar:** `conta_rizoma4/dominio/adaptadores/repositorio_postgres_escritura.py` (separado del importador heredado `repositorio_postgres.py`), `migrations/007_*.sql` sólo si el ensayo exige ajustes y `pilot_incivsa/informe_rollback.md`.
- **Evidencia de cierre:** replicación de la verificación dual sobre entorno aislado y restauración completa ensayada con resultado documentado.

### P5 — Seguridad operativa de la API

- **Funcionalidad:** matriz de permisos por ruta, identidad de actor en cada mutación, limitación de intentos de login y de tamaño/tiempo de petición, health check con dependencias y traza auditable sin secretos en logs.
- **Modificar:** `conta_rizoma4/api/main.py`, `conta_rizoma4/auth.py`, `conta_rizoma4/api/routers/auth.py`, `asientos.py`, `empresas.py`, `documentos.py`, `corpus_forense.py`, `leases.py`, `obras.py`, `operarios.py`, `verificar.py`, `tests/test_api_seguridad_auth.py`, `tests/test_api_corpus.py`, `tests/test_api_custodia.py`.
- **Incorporar:** `conta_rizoma4/api/middleware.py` (límites, identificador de petición y auditoría) y `gobernanza/matriz_permisos_api.md`.
- **Evidencia de cierre:** matriz verificada ruta por ruta, prueba de rechazo de escalada de rol/empresa y configuración de producción sin secretos por defecto.

### P6 — Despliegue y operación

- **Funcionalidad:** imagen reproducible, orquestación local equivalente a producción, CI con revisión, runbook de arranque/parada/backup/rollback y bootstrap administrativo controlado.
- **Modificar:** `README.md`, `Makefile`, `pyproject.toml` (versión), `scripts/crear_admin_inicial.py`, `scripts/migrate.py`, `scripts/worker_leases.py`.
- **Incorporar:** `Dockerfile`, `.dockerignore`, `docker-compose.prod.yml`, `.github/workflows/ci.yml` (sujeto a revisión antes de activarse) y `gobernanza/runbook_produccion.md`.
- **Evidencia de cierre:** despliegue en entorno aislado desde imagen construida, health check con dependencias y ensayo de rollback documentado.

### P7 — Activación de datos reales e INCIVSA

- **Funcionalidad:** criterio para los 108 grupos `NO_DETERMINADO`, revisión humana de los 1.204 borradores, correspondencia de identidades, actuaciones extraordinarias, responsable profesional y ventana reversible.
- **Modificar:** `pilot_incivsa/informe_no_activacion.md`, `informe_migracion_2026-11-25.md`, `expediente.md`, `preflight_migracion_2026-11-25.md`, `scripts/incorporar_incivsa.py`, `conta_rizoma4/dominio/adaptadores/incivsa_lectura.py`, `pilot_incivsa/test_bloqueos.py`, `pilot_incivsa/test_migracion_segura.py`.
- **Incorporar:** `gobernanza/incivsa_criterio.md` y `gobernanza/acta_activacion.md`; `informe_no_activacion.md` sólo puede cambiar de estado con esa acta.
- **Evidencia de cierre:** verificación dual completa y acta firmada; sin ella se mantiene **NO ACTIVADO PARA PERSISTENCIA POSTGRESQL**.

### P8 — Aceptación final

- **Funcionalidad:** declarar el programa cumplido sólo con todas las puertas cerradas y aprobaciones vigentes.
- **Modificar:** `README.md`, `PLAN_CIERRE_BRECHAS.md`, `CHANGELOG.md`, `pyproject.toml` (versión de entrega).
- **Incorporar:** `gobernanza/acta_aceptacion.md`.
- **Evidencia de cierre:** suite unitaria e integración en verde, smoke HTTP con roles reales en entorno aislado, restauración ensayada, verificación dual y actas de autoridad/activación.

Correspondencia con los tramos: P0 ← tramo 0; P1 ← tramos 1 y 2; P2 ← tramos 3 y 7; P3 ← tramos 4, 5 y 6; P4 ← tramo 10; P5 ← tramos 0 y 11; P6 ← infraestructura nueva; P7 ← expediente INCIVSA; P8 ← regla de cierre global.

## Programa priorizado

### Tramo 0 — Restablecer una base verificable y segura

**Objetivo:** que el proyecto importe y se pueda validar sin ambigüedades de dependencias o configuración.

**Trabajo**

- Resolver el import `parsers.contrato_dominio`: determinar si es dependencia externa, paquete omitido o frontera opcional. No reimplementar el contrato por suposición.
- Definir una configuración reproducible de desarrollo/pruebas y una configuración de producción que exija secreto JWT persistente, orígenes CORS explícitos y límites de petición.
- Actualizar README y documentación de API para que describan rutas, roles, scripts y métricas existentes; eliminar afirmaciones de cobertura no demostradas.
- Añadir una matriz de permisos de cada ruta: rol, empresa, identidad del actor, mutaciones y datos expuestos.

**Aceptación**

- La aplicación y sus routers pueden importarse desde una instalación limpia documentada.
- La configuración insegura falla de forma cerrada para producción; no hay comodines de CORS en configuración de producción.
- La documentación coincide con rutas y controles existentes.
- Las pruebas de API pueden recolectarse sin servicios reales y separan claramente las pruebas de integración.

**Bloqueo:** no activar API de producción mientras falle la importación o la matriz de permisos tenga rutas sin responsable.

**Avance 2026-11-25:** se declaró `python-multipart`, requerido directamente por los formularios de carga; la API importa cuando el checkout hermano `rizoma4` está en `PYTHONPATH` y se proporciona una URL PostgreSQL de prueba. Se retiró CORS global por defecto y se actualizaron afirmaciones de cobertura y rutas obsoletas del README. Falta validar instalación limpia reproducible y configuración de despliegue.

### Tramo 1 — Integridad del núcleo y reconstrucción histórica

**Objetivo:** cumplir el requisito central de reconstruir qué ocurrió, qué se conocía, qué decisión regía y qué representación existía en cualquier fecha de conocimiento.

**Trabajo**

- Hacer que reconstrucción derive el estado exclusivamente de eventos inmutables ordenados por tiempo epistémico, no del estado mutable actual de las entidades.
- Incluir en el evento canónico todo dato que se pretenda proteger: estados anterior/posterior, referencias, motivo, identidad, fechas, versión del criterio y payload normalizado.
- Evitar alias mutables: copiar o serializar de forma inmutable los payloads registrados.
- Definir transiciones válidas para hecho, interpretación, decisión, autorización, representación, rectificación y cierre.
- Registrar por separado fecha contable, ocurrencia, conocimiento y registro cuando corresponda.
- Añadir escenarios de reconstrucción antes/después de adopción, revocación, rectificación, reapertura y recepción tardía de evidencia.

**Aceptación**

- Una reconstrucción histórica no cambia si se consulta después de eventos futuros.
- Alterar un estado o payload registrado produce un fallo de verificación.
- Una rectificación conserva la representación original y reconstruye ambas versiones en sus fechas correspondientes.
- El hash se documenta solo como detector de alteraciones dentro del modelo; nunca como prueba de identidad, autenticidad o veracidad.

**Avance 2026-11-25:** los eventos ahora encadenan snapshots anterior/posterior; la reconstrucción deriva de eventos entidades, actores, fuentes, hechos, evidencias/valoraciones, criterios, autorizaciones, interpretaciones, decisiones, representaciones, rectificaciones, ejercicios y cierres. Se separan fechas efectivas/recibidas de fechas de registro para criterios, evidencia y representación. Se añadieron comprobaciones de actor, coherencia decisión-hecho-interpretación y alcance/fecha/segregación básica cuando se aporta autorización. El ledger rechaza fechas de evento regresivas. Las autorizaciones admiten vencimiento y revocación como evento auditable; uso en decisiones, rectificaciones, cierre y reapertura comprueba vigencia para la fecha del acto. Verificado con 30 pruebas focalizadas de núcleo, ejercicios/cierre y seguridad API. Sigue parcial: falta definir la matriz profesional de competencias y cerrar la identidad autenticada del adaptador.

### Tramo 2 — Autoridad, decisiones e identidades

**Objetivo:** que cada acción significativa corresponda a un actor existente y a una autorización competente, delimitada y vigente.

**Trabajo**

- Exigir actor existente en todas las operaciones del núcleo, incluida propuesta de interpretación y asociación/valoración de evidencia.
- Validar autorización en adopción de decisiones, representación, rectificación, cierre y reapertura: emisor, competencia, alcance, vigencia, fecha y separación de funciones que corresponda.
- Verificar que la interpretación adoptada pertenezca al hecho/objeto de la decisión y que la representación cite esa decisión e interpretación coherentes.
- Definir revocación y sustitución de autorizaciones como eventos nuevos, sin borrar historial.
- Mapear identidad autenticada a actor de dominio mediante un puerto explícito; no aceptar nombres o identificadores declarados por el cliente como prueba de identidad.

**Aceptación**

- Actor inexistente, autorización fuera de alcance, posterior al acto o de competencia incorrecta son rechazados.
- Las pruebas muestran separación de creador, decisor, autorizador, visador y aprobador según política aprobada.
- Cada operación conserva actor, motivo, referencias y fecha.

**Decisión requerida antes de cerrar el tramo:** aprobar una matriz de competencias y segregación de funciones por operación; la ingeniería no debe inventar quién tiene autoridad contable o jurídica.

**Avance parcial 2026-11-25:** las autorizaciones pueden caducar y revocarse mediante un evento histórico, y su vigencia temporal se comprueba en operaciones que ya las aceptan. No se considera cerrado el tramo: la autorización para decisiones sigue siendo opcional, la representación no contiene autorización asociada y el núcleo aún no puede verificar que el otorgante tuviera competencia para emitirla. Estas brechas dependen de la matriz aprobada y de una identidad autenticada enlazada a actor.

### Tramo 3 — Fase 2: presentación PGC-PYMES

**Objetivo:** completar los estados de presentación como productos derivados y verificables, sin confundir presentación analítica con formulación o depósito.

**Trabajo**

- Inventariar modelos, partidas, notas y reglas por marco, entidad y ejercicio.
- Versionar reglas de clasificación, agregación y desglose con fuente, vigencia y revisión.
- Completar validaciones aritméticas y relaciones entre estados; mantener separado el juicio de clasificación.
- Incorporar elegibilidad y memoria mínima/adicional solo a partir de criterios aprobados y fuentes oficiales identificadas.
- Añadir trazabilidad desde cada cifra presentada a representaciones, decisiones, criterios y evidencias fuente.

**Aceptación**

- Un paquete de presentación declara marco, ejercicio, versión de reglas, datos omitidos y controles pendientes.
- Los modelos y casos cubiertos tienen pruebas aritméticas y de trazabilidad.
- No se etiqueta como formulable/depositable mientras falten cobertura, elegibilidad o memoria exigida.

**Bloqueo:** decisiones sobre marco, elegibilidad y suficiencia requieren validación contable competente.

### Tramo 4 — Fase 3: cierre integral y reapertura

**Objetivo:** cerrar y reabrir ejercicios conservando autorizaciones, instantáneas, asientos propuestos y reconstrucción temporal.

**Trabajo**

- Completar precondiciones: vencimientos, conciliaciones, periodificaciones, amortizaciones, deterioros, regularización y resultado.
- Hacer explícito qué resultados son propuestas de hoja de trabajo y cuáles se registran como representaciones.
- Añadir idempotencia, bloqueo de periodo y concurrencia por entidad/ejercicio.
- Requerir autorización de cierre/reapertura con alcance y fecha válidos.
- Registrar instantánea de saldos y diferencias para verificar reejecución y reapertura.

**Aceptación**

- No se cierra con controles críticos pendientes sin excepción autorizada y documentada.
- Repetir preparación no duplica operaciones ni muta el mayor.
- La reapertura agrega hechos/eventos y permite reconstruir estados pre y post cierre.

### Tramo 5 — Fase 4: tesorería y conciliación bancaria

**Objetivo:** llevar los movimientos desde el extracto importado hasta su conciliación con evidencia y decisión humanas trazables.

**Trabajo**

- Separar importación de extracto, normalización, propuesta de correspondencia y decisión de conciliación.
- Añadir identificadores idempotentes de origen y conservación íntegra del archivo fuente y su huella.
- Tratar duplicados, cargos parciales, comisiones, fechas de valor, transferencias internas y diferencias sin asiento automático por defecto.
- Añadir revisión y autorización cuando la conciliación origine una representación contable.

**Aceptación**

- Reimportar el mismo extracto no duplica movimientos.
- Toda conciliación enlaza movimiento bancario, movimiento económico, evidencia, actor y criterio.
- Las diferencias y propuestas no se registran silenciosamente como hechos.

### Tramo 6 — Fase 5: facturación ordinaria y rectificaciones

**Objetivo:** completar ciclo de factura, cobro/pago, vencimientos, rectificación y relación con documentos originales.

**Trabajo**

- Completar numeración por entidad/serie/ejercicio con concurrencia y no reutilización.
- Validar impuestos y retenciones mediante reglas versionadas y trazables.
- Modelar rectificativas con vínculo al original, causa, importes, fecha y autorización aplicable.
- Mantener estados administrativos separados de la existencia del hecho económico y del asiento.

**Aceptación**

- No se permite reutilizar numeración ni rectificar sin referencia y motivo.
- La rectificación genera nuevos eventos y representaciones vinculadas; no sobrescribe la factura ni el asiento anterior.
- Los cálculos reproducen la versión de regla aplicada.

### Tramo 7 — Fase 7: fiscalidad versionada

**Objetivo:** evolucionar los modelos básicos actuales hacia cálculos fiscales reproducibles por periodo y versión.

**Trabajo**

- Registrar catálogo oficial de modelos, casillas, regímenes, tipos, límites, calendarios y fuentes con vigencias.
- Separar bases, cuotas, ajustes, compensaciones, retenciones y reglas transitorias.
- Validar elegibilidad por contribuyente, ejercicio y régimen.
- Construir expediente de cálculo con vínculos a libros, evidencias, reglas y decisiones.
- Generar salida de presentación solo tras completar validaciones y revisión profesional.

**Aceptación**

- Un resultado puede reproducirse con la versión exacta de reglas y datos conocidos en su fecha.
- Las casillas no calculadas o fuentes ausentes se identifican como no determinadas, nunca se rellenan por inferencia silenciosa.
- No se afirma presentación ni cumplimiento AEAT sin validar formato, requisitos y canal aplicable.

**Bloqueo:** catálogo y reglas requieren revisión fiscal oficial por ejercicio y régimen.

### Tramo 8 — Fase 1 en cola 2: consolidación normativa completa

No iniciar hasta que el usuario la retire expresamente de `COLA_ESPERA_2.md`. El alcance incluye perímetro, control, participaciones históricas, minoritarios, homogeneización, moneda, intragrupo, eliminaciones aprobadas, goodwill/diferenciales y estados consolidados. Cada eliminación seguirá siendo propuesta hasta decisión y autorización válidas.

### Tramo 9 — Fase 6 en cola 2: inmovilizado y existencias avanzados

No iniciar hasta que el usuario la retire expresamente de `COLA_ESPERA_2.md`. Antes de activar escenarios avanzados, definir con revisión contable los tratamientos de leasing, permutas, deterioros, bajas, costes, FIFO y correcciones de valor que apliquen.

### Tramo 10 — Adaptadores y migración en entorno aislado

**Objetivo:** probar correspondencia y persistencia sin convertir datos heredados en hechos acreditados ni alterar el ledger histórico.

**Trabajo**

- Resolver claves estables y correspondencias para origen código+fecha de INCIVSA.
- Completar verificación dual campo a campo y reconciliar omitidos, importes, hashes, estados, documentos y rectificaciones.
- Implementar escritura append-only real, transacción todo-o-nada, rollback probado y aislamiento por entidad.
- Aplicar mínimo privilegio en PostgreSQL y controles de solo lectura/solo escritura separados.
- Ensayar respaldo y restauración completa; el reconocimiento del archivo de backup no basta.

**Aceptación**

- Ensayo repetido idempotente en base desechable identificada.
- Reconstrucción equivalente entre memoria y PostgreSQL en escenarios acordados.
- Restauración y rollback ejecutados y documentados.
- Sin datos reales cambiados hasta aprobación técnica, contable y jurídica específica.

### Tramo 11 — Seguridad de aplicación y preparación de producción

**Objetivo:** cerrar los riesgos de acceso, abuso, disponibilidad y exposición de datos antes de cualquier operación real.

**Trabajo**

- Aislar corpus y todos los recursos por empresa tanto en consultas como en restricciones de base de datos; la restricción solo a administradores es temporal.
- Sustituir CORS comodín por lista explícita de orígenes y métodos mínimos.
- Incorporar límites en proxy y aplicación: tamaño total, tiempo, concurrencia y tipos de archivos permitidos.
- Aplicar limitación de intentos de login, registro de eventos de seguridad y alertas sin registrar contraseñas/tokens.
- Revisar secretos, rotación, expiración/revocación de sesiones y privilegios de cuentas de servicio.
- Ejecutar revisión de amenazas y pruebas de autorización por rol y empresa; revisar configuración de despliegue y restauración.

**Aceptación**

- Pruebas negativas prueban denegación de acceso cruzado a cada recurso.
- Configuración productiva no contiene claves por defecto, orígenes globales ni credenciales de privilegio excesivo.
- Hay límites y respuesta observables ante abuso de login, cargas y concurrencia.
- Existe acta de revisión de seguridad y aprobación de despliegue.

## Gestión de decisiones y bloqueos

El trabajo técnico puede avanzar en los componentes independientes mientras se esperan decisiones. No se deben cerrar estos puntos por inferencia:

- competencias y segregación de funciones;
- suficiencia de evidencias y aceptación de interpretaciones INCIVSA;
- política de conservación y acceso al corpus forense;
- marco PGC-PYMES, elegibilidad y suficiencia de memoria;
- régimen y reglas fiscales por entidad y ejercicio;
- criterios para operaciones avanzadas de consolidación, inmovilizado y existencias.

Cada decisión pendiente debe registrarse con responsable, evidencia/fuente, alcance, fecha, impacto y estado. Si falta responsable o fuente, el resultado permanece `NO DETERMINADO`.

## Ronda de decisiones por roles — 2026-11-26

- **DOCUMENTADO:** las respuestas A–H del usuario quedan recogidas en `gobernanza/acta_decisiones_roles.md`, con clasificación por decisión y elementos abiertos.
- **VERIFICADO:** `revocar_permiso` registra ahora el estado anterior real y `reconstruir` conserva la concesión al proyectar la revocación, con nuevas pruebas en `tests/test_nucleo_dominio.py`.
- **PROPUESTA:** `gobernanza/acta_aceptacion.md` define el alcance de P8, los invariantes bloqueantes y lo que no autoriza; sigue en `BORRADOR, NO FIRMADA`.
- **VERIFICADO:** la delegación ya está conectada a crear/visar/aprobar asientos desde `dominio_evento`, con pruebas HTTP de activa/revocada y script local de escritura.
- **NO DETERMINADO:** ningún criterio contable, documental, de seguridad ni operativo de esta batería. A3, B1, B2, C3, C4, D3, D4, E1, F2, F3, G2, G4 y H4 quedan confirmados.
- **DOCUMENTADO:** la batería de activación 2027 P0-1…P2-3 quedó `DOCUMENTADO` y `CONFIRMADO` por el responsable el 2026-11-26 en `gobernanza/acta_activacion.md`, en bloque y con mis mejores inferencias, incluida la instalación limpia de P1-1. No equivale a evidencia ejecutada: P1 continúa pendiente de verificación y P8 de firma.

## Estado inicial del programa

- **VERIFICADO el 2026-11-26:** 138 pruebas de dominio/adaptadores/API simulada y 57 pruebas de actos avanzados pasaron; no equivale a suite integral ni cobertura total. La suite completa en este entorno terminó con 47 fallos y 91 errores por dependencias de prueba, firma de casos de uso desactualizada y PostgreSQL sin rol `test`.
- **DOCUMENTADO:** INCIVSA consta incorporada como borradores; 108 grupos permanecen sin determinar hasta aplicar la regla C3 y 1.204 requieren revisión.
- **DOCUMENTADO:** fases 1 y 6 quedan incorporadas en la fase referida por decisión del usuario; el tramo 1 tiene implementación parcial en el núcleo y los actos avanzados heredados están probados, pero no han sido activados por instrucción expresa.
- **PENDIENTE:** validar instalación limpia y despliegue API completos; el smoke de importación usó el checkout hermano en `PYTHONPATH` y URL PostgreSQL ficticia, sin conexión.
- **PENDIENTE:** verificar la segmentación por empresa y los permisos expresos en un entorno aislado con PostgreSQL antes de considerar fiable el ledger del dominio.
- **NO AUTORIZADO POR ESTE PLAN:** aplicar migraciones, desplegar, activar persistencia productiva o aprobar asientos y declaraciones.

## Regla de cierre global

El programa sólo podrá declararse cumplido cuando cada tramo activo tenga funcionalidad demostrable, pruebas relevantes, historial reconstruible, controles de acceso verificados, documentación fiel, decisiones contables/jurídicas registradas y evidencia de aceptación en el entorno previsto. La existencia de módulos, modelos, hashes o pruebas aisladas no basta. La evaluación se hace con las puertas P0-P8 de la sección «Ruta a producción: funcionalidades y archivos»; la activación de producción queda fuera del programa y exige las actas indicadas.

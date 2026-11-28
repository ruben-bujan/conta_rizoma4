# Acta de decisiones por roles — BORRADOR

Estado: **BORRADOR, PENDIENTE DE FIRMA**. La batería A–H quedó cerrada el 2026-11-26: todas las decisiones del usuario están `DOCUMENTADO y CONFIRMADO` y no queda regla `NO DETERMINADO` en esta acta. La firma sigue sin autorizar activación de producción ni datos reales sin acta específica.

Fecha: 2026-11-26.

Responsable declarado para esta ronda: usuario (`YO`), con alias funcional `DIRECTOR (responsable del proyecto)` aceptado para la beta; el dato real se reserva para el acta de activación.

## A — Dirección

- **A1 — DOCUMENTADO:** INCIVSA se usa como *sparring*/entrenamiento. Si la manipulación afecta al expediente, carece de importancia mientras la causa quede conocida y registrada. Esto no activa producción ni convierte los borradores en aprobados.
- **A2 — DOCUMENTADO:** las fases 1 y 6 se incorporan en la fase referida, no quedan en espera. `COLA_ESPERA_2.md` debe actualizarse en consecuencia.
- **A3 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** los hechos pasados pueden asentarse cuando sea posible, con informe de `JEFE_CONTABILIDAD`, `SUBDIRECTOR` o `DIRECTOR` según clasificación, referenciando el momento en que normalmente se habría contabilizado. El efecto previo viaja como metadato/informe; la cadena hash no se reescribe.
- **A4 — DOCUMENTADO:** se aclara el alcance de `gobernanza/acta_aceptacion.md` en ese archivo: es la puerta final P8, no una autorización de INCIVSA real ni un alta en producción.

## B — Técnico

- **B1 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** se mantiene HS256 y expiración de 24 h. Hoy `conta_rizoma4/auth.py:15` usa `CONTA_JWT_SECRET` o un valor aleatorio temporal, con guardia de producción (`auth.py:20-31`). En producción el secreto se inyecta desde el bundle `secrets` por nombre al entorno de ejecución, nunca desde `.env` versionado; rotación cada 90 días y ante incidente por `ADMIN de operación` con autorización de `DIRECTOR`. La rotación invalida tokens y obliga a nuevo login; no se añade lista de revocación en esta beta.
- **B2 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** `conta_rizoma4/api/main.py:42-53` exige orígenes explícitos, sin comodín, con `allow_credentials=False`. En la beta la lista queda vacía porque el frontend se sirve desde la misma API; en producción se completarán orígenes exactos `https://...` antes de la activación, sin `*`.
- **B3 — DOCUMENTADO:** se acepta `scripts/migrate.py` tal cual (`scripts/migrate.py:10-28`). La reversibilidad depende de copia/restauración ensayada fuera del script.
- **B4 — DOCUMENTADO:** se aprueba repositorio externo separado y append-only para la escritura segura.

## C — Contable

- **C1 — DOCUMENTADO:** se aprueba la versión de catálogo propuesta.
- **C2 — DOCUMENTADO:** el cierre queda como condición de bloqueo de la operación correspondiente.
- **C3 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** redondear cada fila original a céntimos con `ROUND_HALF_UP`, sumar las líneas ya redondeadas y conservar el importe original y la diferencia como metadato. Si un grupo no cuadra tras el redondeo, permanece `NO_DETERMINADO` para revisión humana; no se crea asiento de ajuste automático.
- **C4 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** para un ejercicio pasado de cuatro años sin incidencias judiciales/administrativas, se admite un único asiento de cierre. Con incidencias pendientes se exigen las garantías de la contabilidad vigente salvo que `DIRECTOR` asuma responsabilidad y fije límites. Todo asiento con terceros vincula documento. La revisión cubre el 100 % de los 10 asientos de mayor importe y de todo asiento con tercero vinculado, incidencia o ajuste manual; del resto se toma `max(30, ceil(10 %))` con semilla aleatoria registrada. Cualquier desviación en la revisión completa bloquea el lote; más de 2 desviaciones en el aleatorio obliga a revisar el 100 %. Se registran hash del documento, id del asiento, selección, resultado, revisor y fecha. ISA 530 no fija porcentaje: esta regla es el criterio operativo adoptado para la beta.

## D — Jurídico

- **D1 — DOCUMENTADO:** se confirma el marco extraordinario de INCIVSA.
- **D2 — DOCUMENTADO:** la criticidad alta afecta a la imagen fiel; la inferior afecta a principios contables de segundo orden.
- **D3 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** el CSV de sparring vale como fuente documental de entrenamiento si lleva hash del fichero y referencia de fila. No sostiene asientos aprobados ni asientos con terceros reales: éstos exigen documento externo vinculado por hash. Los borradores sin documento quedan excluidos de aprobación.
- **D4 — DOCUMENTADO con alias funcional aceptado para la beta:** la responsabilidad final es de `DIRECTOR`; para este proyecto, del usuario (`YO`), representado como `DIRECTOR (responsable del proyecto)`. El nombre real se completará sólo en el acta de activación.

## E — Seguridad y datos

- **E1 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** CIMA queda fuera de la beta; no se carga en corpus ni se indexa. INCIVSA continúa como sparring sintético/anonymizado. No se borran ficheros existentes sin autorización. Riesgo técnico observado: el corpus permite `nombre`, `nif` y metadatos (`conta_rizoma4/corpus_forense/modelo.py:14-22`) y su endpoint no aísla por empresa (`api/routers/corpus_forense.py:22-28`); queda como alarma para cualquier inclusión futura.
- **E2 — DOCUMENTADO:** login con 3 intentos y bloqueo de 3 minutos.
- **E3 — DOCUMENTADO:** prohibir en logs `NIF`, `CIF`, nombres propios y hashes; aplica también a errores y trazas.
- **E4 — DOCUMENTADO y VERIFICADO:** `aux_obra` mapea a `AUXILIAR` por defecto (`api/deps.py:8-13`). Bajo orden vigente de `JEFE_CONTABILIDAD` puede actuar con efectos de `OPERARIO` mediante permiso expreso vigente en `dominio_evento`, sin promover el rol persistido. `usuario_con_competencia` conecta esa delegación a crear/visar/aprobar asientos; `scripts/gestionar_permiso.py` escribe la concesión y la revocación. Cubierto por `tests/test_api_delegacion_eventos.py`.

## F — Delegación, retención y jerarquía

- **F1 — INFERIDO:** el usuario no recordaba el origen de la pregunta; la investigación anterior dejó evidencia de exposición de identidad en corpus e INCIVSA. Véase E1.
- **F2 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** la delegación ordinaria corresponde a `JEFE_CONTABILIDAD` y puede recaer en `OPERARIO`, con otorgante, beneficiario, competencia, alcance, vigencia, motivo y trazabilidad ya registrados en el núcleo (`conta_rizoma4/dominio/entidades/contables.py:193-202`, `nucleo.py:733-797`, `:909-930`). Vigencia por defecto de 90 días, renovable sólo con nuevo evento `PERMISO_CONCEDIDO`, sin renovación silenciosa. Visado posterior dentro de 24 h para `ASIENTO_DIARIO` ordinario; visado previo obligatorio de `JEFE_CONTABILIDAD` o `SUBDIRECTOR` para `ASIENTO_VISAR`, `ASIENTO_APROBAR`, rectificaciones, cierres y reaperturas. Sin delegación de cierre/reapertura a `OPERARIO` salvo permiso explícito de `SUBDIRECTOR`.
- **F3 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** conservar libros, justificantes, documentos y trazabilidad 6 años desde el último asiento del ejercicio, prorrogando a 10 años cuando haya créditos o deducciones bajo comprobación. Acceso por rol y necesidad de conocimiento, con `ADMIN` sólo en custodia. Nombre y NIF seudonimizados salvo requerimiento legal autorizado por `DIRECTOR`; nunca NIF/CIF/nombres/hashes en logs. Tras el plazo, borrar o anonimizar el contenido sólo con acta firmada de `ADMIN` y `DIRECTOR`, conservando la cadena de hashes y los metadatos de auditoría.
- **F4 — DOCUMENTADO:** la responsabilidad sigue la concesión `DIRECTOR > SUBDIRECTOR > JEFE_CONTABILIDAD`.

## G — Operación

- **G1 — DOCUMENTADO:** despliegue en servidor propio con Docker/compose y CI revisada.
- **G2 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** `ADMIN` ejecuta y conserva las copias. En beta: `pg_dump -Fc` diario cifrado fuera del servidor, 30 copias diarias y 12 mensuales, RPO ≤24 h y RTO ≤4 h, con prueba de restauración aislada antes de activar y cada mes. Producción añade archivado WAL y base backup semanal si se requiere PITR; no se borran copias dentro de la retención sin acta. `pg_dump` queda documentado como copia lógica, no como mecanismo PITR por sí solo.
- **G3 — DOCUMENTADO:** en esta beta el usuario asume los cambios de código. Con licencia y entrega de fuentes, `ADMIN` actúa con autorización de `SUBDIRECTOR` para acciones no críticas y de `DIRECTOR` para críticas.
- **G4 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** ventana de 72 h desde instantánea con hash verificado y restauración probada en copia aislada. `ADMIN` puede pausar de inmediato y `DIRECTOR` ordenar rollback. Durante la ventana no se aprueban asientos ni declaraciones reales, no se borran datos y toda escritura irreversible queda fuera. Cierre o prórroga exige acta firmada; no hay prórroga automática.

## H — Auditoría

- **H1 — DOCUMENTADO:** ejecutar todas las pruebas posibles disponibles en el entorno; suites segura e `integration` ya ejecutadas.
- **H2 — DOCUMENTADO:** para esta beta basta con datos PGC sintéticos.
- **H3 — DOCUMENTADO:** revisor independiente ahora el usuario; en producción con entrega de fuentes, `ADMIN`.
- **H4 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** son bloqueantes absolutos los 9 invariantes de `gobernanza/acta_aceptacion.md`; las desviaciones doctrinales se registran como alarma con responsable y fecha, sin bloquear por sí solas.

## Cambios implementados con esta ronda

- **VERIFICADO:** `revocar_permiso` conserva ahora el estado anterior real en el evento, en lugar de registrar dos veces el estado ya mutado (`conta_rizoma4/dominio/servicios/nucleo.py:791-796`).
- **VERIFICADO:** `reconstruir` conserva la concesión al proyectar la revocación (`nucleo.py:1259-1263`).
- **VERIFICADO:** nuevas pruebas de delegación vigente/alcance, revocación y reconstrucción histórica en `tests/test_nucleo_dominio.py`.
- **VERIFICADO:** delegación de `dominio_evento` cableada en crear/visar/aprobar asientos y escrita por `scripts/gestionar_permiso.py`, con pruebas HTTP de `403`/`201`/`403` en `tests/test_api_delegacion_eventos.py`.

# Acta de activación contable 2027 — BORRADOR

Estado: **BORRADOR, PENDIENTE DE FIRMA**. Las 19 decisiones P0-1…P2-3 quedan `DOCUMENTADO` y `CONFIRMADO` por el responsable el 2026-11-26, incluida la instalación limpia de P1-1. Las evidencias de P1 no están ejecutadas y P8 no está firmado: esto no autoriza activación de producción, persistencia de datos reales ni aprobación contable.

Fecha: 2026-11-26.

Objeto: activación de la contabilidad de una persona jurídica el 2027-01-01, tras el cierre del ejercicio 2026.

Clasificación usada: **VERIFICADO**, **DOCUMENTADO**, **INFERIDO**, **PROPUESTA**, **NO DETERMINADO**.

## Responsables

- `DIRECTOR (responsable del proyecto)`: alias funcional aceptado para la beta; dato real pendiente de incorporar en esta acta antes de la firma.
- `SUBDIRECTOR`: alias funcional para las autorizaciones de cierre y reapertura; dato real pendiente.
- `ADMIN de operación`: alias funcional para custodia, copias y parada; dato real pendiente.
- `Revisor independiente (usuario en beta)`: alias funcional; dato real pendiente.

No se escriben nombres, NIF, CIF, credenciales ni secretos en la conversación ni en ficheros versionados.

## Decisiones de activación

### P0 — Antes de tocar datos reales

- **P0-1 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** los responsables reales de `DIRECTOR`, `SUBDIRECTOR`, `ADMIN` y revisor se incorporan sólo a esta acta firmada. Hasta entonces se usan los alias funcionales anteriores. La firma no autoriza por sí sola producción: queda supeditada al cierre del resto de decisiones y evidencias.
- **P0-2 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** ventana de activación del 2027-01-01 00:00 al 2027-01-04 00:00 desde instantánea del 2026-12-31 23:59 con hash verificado y restauración ensayada en copia aislada. `ADMIN` puede pausar de inmediato y `DIRECTOR` ordenar rollback. Dentro de la ventana no se aprueban asientos ni declaraciones reales, no se borran datos y toda escritura irreversible queda fuera. Cierre o prórroga exige acta firmada; no hay prórroga automática.
- **P0-3 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** la producción corresponde a una persona jurídica española con `empresa_id` asignado en esta acta, moneda EUR y ejercicio natural 01-01→12-31. El marco es `PGC_ES`; se aplica PGC-PYMES sólo si la entidad cumple los umbrales, y PGC completo en caso contrario. La elegibilidad concreta queda supeditada a P2-2. No se incorporan denominación, NIF ni otros datos sensibles a la conversación ni a ficheros versionados.
- **P0-4 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** la fuente del cierre 2026 es el balance de comprobación, el inventario y las conciliaciones exportados del sistema actual a 31/12/2026, con hash y certificación del responsable contable. Todo ajuste manual exige documento fuente vinculado y aprobación; el cálculo del núcleo no sustituye la revisión humana prevista en `conta_rizoma4/dominio/casos_uso/cierre.md:18`. No se introducen datos reales en la conversación ni en ficheros versionados.
- **P0-5 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** el efecto económico del cierre 2026 es 31/12/2026 23:59; la fecha de conocimiento y la de registro son el momento real de ejecución. El efecto previo viaja como metadato e informe de `JEFE_CONTABILIDAD`, `SUBDIRECTOR` o `DIRECTOR` según A3, sin backdating ni reescritura de la cadena hash.
- **P0-6 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** el cierre y, si hiciera falta, la reapertura del ejercicio 2026 los autoriza nominalmente `SUBDIRECTOR` con alcance `ejercicio 2026`, fecha de efecto 31/12/2026 y motivo expreso. La autorización lleva contrafirma de `DIRECTOR` y revisión del revisor independiente, con identidad real incorporada al firmar. No se delega en `OPERARIO` salvo permiso explícito de `SUBDIRECTOR` según F2.
- **P0-7 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** aprobado el cierre 2026, se crea el ejercicio 2027 en estado `ABIERTO` y la propuesta inversa de `conta_rizoma4/dominio/casos_uso/cierre.md:27` se convierte en representación contabilizada con efecto 01/01/2027 00:00, documento fuente vinculado y autorización vigente. No hay contabilización automática de las líneas propuestas.
- **P0-8 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** no hay incidencias judiciales ni administrativas pendientes para los ejercicios 2026 y 2027. Si aparecen, se listan en esta acta y se aplican las garantías de la contabilidad vigente con límites fijados por `DIRECTOR`, sin usar la vía simplificada de C4.
- **P0-9 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** INCIVSA queda excluido de la persona jurídica real. Los 1.204 borradores y 108 grupos de `pilot_incivsa/informe_migracion_2026-11-25.md` conservan su carácter de sparring/entrenamiento; no se aprueban, migran ni activan el 01/01/2027 y sigue vigente `pilot_incivsa/informe_no_activacion.md`.
- **P0-10 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26:** P8 es la puerta final y se firma sólo cuando P0-1…P0-9 y las evidencias P1/P2 estén cerradas. La firma incluye los 9 invariantes bloqueantes de `gobernanza/acta_aceptacion.md`, con `ADMIN`, `DIRECTOR` y revisor independiente. Sin esa firma no hay activación ni datos reales.

### P1 — Evidencia técnica antes de activar

- **P1-1 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26, en bloque:** se incorpora la instalación limpia a P1. Deben existir `compose` de producción, CI que ejecute el DDL canónico y las suites, y `gobernanza/runbook_produccion.md`. Criterio de aceptación: un clone limpio arranca y el smoke pasa sin datos reales.
- **P1-2 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26, en bloque:** se congela un orden DDL canónico que excluye `migrations/005_dominio_epistemico.sql:2` (`NO EJECUTAR`), corrige el nombre fijo de base en `migrations/002_worker_user.sql:7` y el bloque `DO $$` anidado de `scripts/ddl_multi_tenant.sql`, y ensaya los triggers de `migrations/004_inmutabilidad.sql` en entorno aislado. No se aplican cambios destructivos a bases existentes.
- **P1-3 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26, en bloque:** la API aplica 3 intentos y 3 minutos de bloqueo por usuario y un límite global; `corpus_forense.py` filtra por `empresa_id`; la matriz de competencias se aplica por ruta; `admin` no tiene bypass implícito. Quedan prohibidos en logs NIF, CIF, nombres propios y hashes, según la decisión del responsable.
- **P1-4 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26, en bloque:** antes de asignar el siguiente número se adquiere bloqueo sobre el contador, con reintento en conflicto y `FOR UPDATE` también en `rizumizar`, para cerrar la carrera de `conta_rizoma4/api/routers/asientos.py:186-190`.
- **P1-5 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26, en bloque:** el backup es ejecutable: `pg_dump -Fc` cifrado y verificado con `pg_restore --list`, con ensayo de restauración completa en entorno aislado antes de P8. Esta evidencia sustituye la afirmación no verificada de `gobernanza/acta_aceptacion.md:17` frente a `pilot_incivsa/informe_migracion_2026-11-25.md:37`.
- **P1-6 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26, en bloque:** antes de P8 la suite `integration` pasa con el DDL canónico y el trigger `004`, y se ejecuta un smoke HTTP con los roles reales sobre datos sintéticos. Sin estas evidencias no se firma P8.

### P2 — Alcance posterior y condiciones fiscales

- **P2-1 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26, en bloque:** las 115 actas del corpus son apoyo técnico, no fuente normativa. Sólo pasan a fuente de trabajo cuando `JEFE_CONTABILIDAD` o `SUBDIRECTOR` revisa referencia, vigencia y aplicabilidad.
- **P2-2 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26, en bloque:** no se emiten modelos 200/303 ni declaraciones hasta confirmar el régimen IS/IVA por `JEFE_CONTABILIDAD` o `SUBDIRECTOR`. La elección entre PGC-PYMES y PGC completo de P0-3 se verifica con documentación de la entidad antes de P8; no se infiere del catálogo.
- **P2-3 — DOCUMENTADO y CONFIRMADO por el responsable el 2026-11-26, en bloque:** el sistema entrega un paquete exportable para cuentas anuales y libros; la formulación, legalización y depósito quedan fuera de la activación y bajo responsabilidad humana expresa. No se afirma presentación telemática realizada.

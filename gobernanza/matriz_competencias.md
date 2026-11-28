# Matriz de competencias — APROBADA

Estado: **APROBADA** por `Rubén` el 2026-11-26. Todas las filas de esta matriz
tienen responsable, rol, alcance y vigencia. El acta de aprobación es
`gobernanza/acta_aprobacion_matriz_competencias.md`.

## Evidencia considerada

- Jerarquía y roles en `conta_rizoma4/dominio/entidades/contables.py`.
- Guardas explícitas por rol en `conta_rizoma4/dominio/servicios/nucleo.py`:
  modo extraordinario, avocación/inhibición, visado de registros sin asiento,
  intervención ADMIN, remisión a investigación y registro contable sin asiento.
- Diseño previo de `verificar_competencia`, con comprobación de jerarquía y de
  permisos expresos vigentes.
- Escala de criticidad por importe de `evaluar_criticidad_importe`, con umbral
  crítico del 20 % del beneficio industrial anterior.
- Instrucciones del usuario: «aprobado» y, tras la consulta de las cinco
  operaciones pendientes, `Aprobar propuesta (Recommended)`.

## Matriz aprobada

| Competencia | Rol aprobado | Alcance | Base | Estado |
| --- | --- | --- | --- | --- |
| `REGISTRO_NO_ASIENTO` | ejecución: `JEFE_CONTABILIDAD`; visado: `SUBDIRECTOR` | registro | Guardas explícitas en `registrar_registro_no_asiento` y `registrar_visado` | APROBADO |
| `MODO_EXTRAORDINARIO_CRITICO` | `DIRECTOR` | entidad | Guarda explícita en `cambiar_modo_contabilidad` | APROBADO |
| `MODO_EXTRAORDINARIO_NOCRITICO` | `SUBDIRECTOR` o `DIRECTOR` | entidad | Guarda explícita en `cambiar_modo_contabilidad` | APROBADO |
| `INTERVENCION_ADMIN` | solicitud: `JEFE_CONTABILIDAD` o `DIRECTOR`; destino: `ADMIN` | solicitud | Guardas explícitas en `solicitar_intervencion_admin` | APROBADO |
| `INFORME_ADMIN` | redacción: `JEFE_CONTABILIDAD`; validación: `JEFE_CONTABILIDAD`, `SUBDIRECTOR` o `DIRECTOR` | informe | Guardas explícitas en `presentar_informe_admin` y `validar_informe_admin` | APROBADO |
| `REMISION_INVESTIGACION` | `JEFE_CONTABILIDAD`, `SUBDIRECTOR` o `DIRECTOR` | hecho económico | Guarda explícita en `registrar_remision_investigacion` | APROBADO |
| `ALERTA_CRITICIDAD` | `DIRECTOR` desde 20 %; `SUBDIRECTOR` desde 13,3333333333 %; informativa por debajo | entidad/importe | `evaluar_criticidad_importe` | APROBADO |
| `DECISION` | `JEFE_CONTABILIDAD` | ejercicio del hecho afectado | Aprobación del usuario; `verificar_competencia` en `adoptar_decision` | APROBADO |
| `REPRESENTACION` | `JEFE_CONTABILIDAD` | ejercicio del hecho afectado | Aprobación del usuario; `verificar_competencia` en `crear_representacion` | APROBADO |
| `ASIENTO_DIARIO` | `JEFE_CONTABILIDAD` | ejercicio del hecho afectado | Aprobación del usuario; `verificar_competencia` en `crear_representacion` | APROBADO |
| `RECTIFICACION` | `JEFE_CONTABILIDAD` | ejercicio del hecho afectado | Aprobación del usuario; `verificar_competencia` en `crear_rectificacion` | APROBADO |
| `CIERRE_EJERCICIO` | `SUBDIRECTOR` | ejercicio | Aprobación del usuario; `verificar_competencia` en `registrar_cierre_ejercicio` | APROBADO |
| `REAPERTURA_EJERCICIO` | `SUBDIRECTOR` | ejercicio | Aprobación del usuario; `verificar_competencia` en `registrar_reapertura_ejercicio` | APROBADO |

Los roles aprobados funcionan como umbral jerárquico: el titular de un rol igual
o superior puede ejecutar la competencia. Un permiso expreso vigente, concedido
según la cadena jerárquica del núcleo, puede habilitar también la operación
conforme al diseño existente de `verificar_competencia`. `ADMIN` no se usa como
umbral de estas competencias contables.

## Vigencia y revocación

Vigencia: desde 2026-11-26 hasta revocación expresa del responsable.

Revocación: por nueva acta del responsable. La revocación de permisos
individuales sigue limitada a quien los concedió, según el núcleo.

## Delegación, revocación y visado

`aux_obra` mapea a `AUXILIAR` por defecto (`conta_rizoma4/api/deps.py:8-13`). La
actuación con efectos de `OPERARIO` no se consigue promoviendo el rol persistido,
sino mediante un permiso expreso vigente concedido por `JEFE_CONTABILIDAD` o
superior: `conta_rizoma4/dominio/entidades/contables.py:193-202` y
`conta_rizoma4/dominio/servicios/nucleo.py:733-797`. `verificar_competencia`
comprueba beneficiario, competencia, alcance, vigencia y no revocación
(`nucleo.py:799-831`). La revocación conserva el estado anterior en el evento y
`reconstruir` mantiene la concesión histórica; queda cubierto por pruebas en
`tests/test_nucleo_dominio.py`.

El visado queda trazado como `VISADO_REGISTRADO` (`nucleo.py:909-929`). La
delegación ya está conectada a la API: `usuario_con_competencia` en
`conta_rizoma4/api/deps.py` consulta `dominio_evento` mediante
`RepositorioPermisosEvento`, mapea `aux_obra` a `OPERARIO` sólo mientras el
permiso esté vigente, y aplica `verificar_competencia` antes de crear, visar o
aprobar asientos (`conta_rizoma4/api/routers/asientos.py`). `admin` conserva su
acceso administrativo previo y no requiere permiso contable de delegación.

La escritura del ledger es local y consciente: `scripts/gestionar_permiso.py`
con `conceder`/`revocar` y `--confirmar`, sobre `dominio_evento`. No existe Alta
pública de permisos.

## Estado técnico

`verificar_competencia` está enlazada a las seis operaciones de la matriz que
antes carecían de control de rol: `adoptar_decision`, `crear_representacion`,
`crear_rectificacion`, `registrar_cierre_ejercicio`,
`registrar_reapertura_ejercicio` y la comprobación de asiento diario dentro de
`crear_representacion`. El mapeo de identidad a `Actor` en
`conta_rizoma4/api/deps.py` (`aux_obra`→`AUXILIAR`, `visador`→`JEFE_CONTABILIDAD`,
`aprobador`→`SUBDIRECTOR`, `admin`→`ADMIN`) ya está cableado en las tres
operaciones de asientos indicadas.

Última verificación, ya posterior al cableado de esta ronda: suite segura
`371 passed, 185 deselected, 1 warning in 2.81s`; suite `integration`
`185 passed, 371 deselected, 1 warning in 13.32s` contra PostgreSQL efímero con
DDL/migraciones aisladas y datos PGC sintéticos. Incluye tres pruebas HTTP de
delegación activa, sin delegación y revocada, más una prueba real del CLI de
concesión y revocación. El clúster efímero fue detenido y eliminado; no se usaron
datos reales ni PostgreSQL de producción.

# Acta de aprobación de la matriz de competencias

Fecha: 2026-11-26

Responsable: Rubén (propietario de la sesión).

Evidencia: instrucción del usuario «aprobado» recibida después de presentar
`gobernanza/matriz_competencias.md` como propuesta, y respuesta
`Aprobar propuesta (Recommended)` a la consulta posterior sobre las cinco
operaciones pendientes.

Objeto: aprobación íntegra de la matriz de competencias, incluidas las filas que
estaban marcadas `NO DETERMINADO`: `ASIENTO_DIARIO`, `DECISION`,
`REPRESENTACION`, `RECTIFICACION`, `CIERRE_EJERCICIO` y
`REAPERTURA_EJERCICIO`.

## Alcance aprobado

- `REGISTRO_NO_ASIENTO`: ejecución por `JEFE_CONTABILIDAD`, visado por
  `SUBDIRECTOR`.
- `MODO_EXTRAORDINARIO_CRITICO`: `DIRECTOR`.
- `MODO_EXTRAORDINARIO_NOCRITICO`: `SUBDIRECTOR` o `DIRECTOR`.
- `INTERVENCION_ADMIN`: solicitud de `JEFE_CONTABILIDAD` o `DIRECTOR`, destino
  `ADMIN`.
- `INFORME_ADMIN`: redacción por `JEFE_CONTABILIDAD`; validación por
  `JEFE_CONTABILIDAD`, `SUBDIRECTOR` o `DIRECTOR`.
- `REMISION_INVESTIGACION`: `JEFE_CONTABILIDAD`, `SUBDIRECTOR` o `DIRECTOR`.
- `ALERTA_CRITICIDAD`: `DIRECTOR` desde 20 %; `SUBDIRECTOR` desde
  13,3333333333 %; informativa por debajo.
- `DECISION`, `REPRESENTACION`, `ASIENTO_DIARIO` y `RECTIFICACION`:
  `JEFE_CONTABILIDAD`, con alcance por ejercicio del hecho afectado.
- `CIERRE_EJERCICIO` y `REAPERTURA_EJERCICIO`: `SUBDIRECTOR`, con alcance por
  ejercicio.

Los roles aprobados operan como umbral jerárquico. Los permisos expresos
vigentes concedidos por un superior jerárquico siguen siendo válidos según el
diseño de `verificar_competencia`. `ADMIN` no se usa como umbral de estas
competencias contables.

Vigencia: desde la fecha de esta acta hasta revocación expresa del responsable.

Revocación: por nueva acta del responsable; la revocación de permisos
individuales sigue limitada a quien los concedió, según el núcleo.

## Efecto técnico

Las guardas por rol ya presentes en `conta_rizoma4/dominio/servicios/nucleo.py`
quedan aprobadas y no se duplican. Quedan enlazadas a `verificar_competencia`
las operaciones `adoptar_decision`, `crear_representacion`,
`crear_rectificacion`, `registrar_cierre_ejercicio` y
`registrar_reapertura_ejercicio`, además de la comprobación de
`ASIENTO_DIARIO` dentro de `crear_representacion`. La API expone `actor_id` y
mapea `aux_obra`→`AUXILIAR`, `visador`→`JEFE_CONTABILIDAD`,
`aprobador`→`SUBDIRECTOR` y `admin`→`ADMIN` en `conta_rizoma4/api/deps.py`.

Verificación: `368 passed, 182 deselected, 1 warning in 2.66s` con
`pytest -q` y `PYTHONDONTWRITEBYTECODE=1` con `PYTHONPATH` de los checkouts
locales. Suite `integration`: `182 passed, 368 deselected, 1 warning in 12.90s`
contra PostgreSQL efímero y datos PGC sintéticos; no se usaron datos reales ni
PostgreSQL de producción.

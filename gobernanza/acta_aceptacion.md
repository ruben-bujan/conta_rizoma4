# Acta de aceptación final — BORRADOR

Estado: **BORRADOR, NO FIRMADA**. No autoriza activación de producción, persistencia de datos reales ni aprobación contable de INCIVSA.

Fecha: 2026-11-26.

## Objeto

Declarar, cuando se firme, que el programa `PLAN_CIERRE_BRECHAS.md` quedó cumplido en el alcance que esta acta identifica. Es la puerta final P8 (`PLAN_CIERRE_BRECHAS.md:103-108`).

## Alcance que cubre cuando se firme

- Cierre de P0 y del trabajo técnico de P1 registrado en `COLA_ESPERA.md`.
- Matriz de competencias aprobada y su evidencia (`gobernanza/matriz_competencias.md`).
- Cadena de eventos, reconstrucción histórica, delegación, revocación y visado implementados en el núcleo.
- Ejecución de las suites segura e `integration` sobre PostgreSQL aislado con datos PGC sintéticos.
- Restauración ensayada y verificación dual documentadas en el expediente del lote correspondiente.

## Alcance que no cubre

- Activar INCIVSA en persistencia PostgreSQL ni convertir sus 1.204 borradores en aprobados.
- Aprobar los 108 grupos `NO_DETERMINADO` sin aplicar la regla C3 ni revisar los descuadres.
- Sustituir la documentación fuente exigida para asientos con terceros.
- Fijar secretos JWT, orígenes CORS, backup/retención o ventana reversible sin sus actas específicas.
- Considerar cerradas las fases 1 y 6 sin el acta que las incorpora.

## Evidencia pendiente de incorporar antes de la firma

- **VERIFICADO:** suite segura `371 passed, 185 deselected, 1 warning in 2.81s`; suite `integration` `185 passed, 371 deselected, 1 warning in 13.32s` contra PostgreSQL efímero, ya eliminado. Incluye delegación activa/revocada en HTTP y prueba real del CLI de permisos.
- **VERIFICADO:** confirmación expresa de A3: efecto previo como metadato/informe, sin reescritura de la cadena hash.
- **VERIFICADO:** C3 confirmado: redondeo por fila a céntimos con `ROUND_HALF_UP`; C4 confirmado: muestreo 100 % en riesgo y `max(30, ceil(10 %))` en el resto.
- **VERIFICADO:** D3 confirmado: CSV sólo como fuente de entrenamiento con hash y referencia de fila; E1 confirmado: CIMA fuera de la beta.
- **VERIFICADO:** G2 confirmado: copia diaria cifrada, 30/12 retención, RPO ≤24 h y RTO ≤4 h; G4 confirmado: ventana 72 h, parada de `ADMIN` y rollback de `DIRECTOR`; F2 confirmado: delegación 90 días con visado posterior en ordinarias y previo en críticas; F3 confirmado: retención 6/10 años, seudonimización y borrado sólo con acta; D4 cubierto con alias funcionales para la beta.
- **VERIFICADO:** smoke HTTP con roles reales en entorno aislado: sin delegación `403`, con delegación vigente `201`, tras revocación `403`.
- **VERIFICADO:** B1 y B2 confirmados: secreto JWT inyectado desde `secrets` con rotación 90 días/incidente; CORS beta sin orígenes externos y producción con lista exacta pendiente.

## Invariantes bloqueantes confirmados

1. No borrar ni reescribir asientos, líneas ni eventos; las correcciones son append-only.
2. Todo asiento cuadra en debe/haber y la cadena hash es válida.
3. Toda mutación tiene actor autenticado, rol, empresa y autorización vigente.
4. Existe aislamiento por empresa.
5. Las fechas económica, de conocimiento y de registro están separadas; no se falsifica el pasado.
6. INCIVSA no se publica como aprobado sin acta firmada.
7. No aparecen secretos, NIF, CIF, nombres propios ni hashes en logs o respuestas.
8. La documentación fuente exigida está vinculada al asiento correspondiente.
9. La copia previa existe y la restauración fue ensayada.

Cualquier violación de estos invariantes bloquea. Toda desviación doctrinal distinta se registra como alarma con responsable y fecha, sin bloquear por sí sola.

## Firmantes

- `DIRECTOR (responsable del proyecto)`: alias funcional aceptado para la beta; dato real reservado al acta de activación.
- `ADMIN de operación`: alias funcional aceptado para la beta.
- `Revisor independiente (usuario en beta)`: alias funcional aceptado; en producción, `ADMIN` con entrega de fuentes.

# Preparación de migración PostgreSQL aislada

## Verificado en esta iteración

- La verificación dual compara cardinalidad, presencia, entidad e índice, fechas, conceptos, hashes, estados, debe/haber y los campos extendidos disponibles para líneas, documentos, rectificaciones, actor, autorización, evidencia, fuentes, decisión, interpretación y ejercicio.
- Bloquea activación por claves incompletas/duplicadas, diferencias, correspondencias ausentes/sobrantes/duplicadas, destino duplicado, tipos incompatibles o importaciones marcadas como acreditadas.
- El importador valida que todos los asientos recibidos pertenezcan a la empresa solicitada y que sus índices sean positivos y no duplicados.
- El ensayo llama a rollback ante éxito y también ante error. Las pruebas usan conexiones simuladas.

## No ejecutado ni verificado

No se conectó a PostgreSQL, no se ejecutaron DDL/migraciones ni se persistieron datos. Las pruebas simuladas verifican el flujo de llamadas, pero no prueban rollback físico, aislamiento transaccional, restricciones, índices, permisos, compatibilidad de esquema ni rendimiento.

Antes de un ensayo físico se requiere una instancia desechable aislada, DDL revisado y aprobado, copia/restauración verificable, fixtures sintéticos por empresa y aprobación técnica, contable y jurídica. El ensayo debe probar confirmación y rollback, comparar lecturas completas, revisar correspondencias de actores/autorizaciones/evidencias/ejercicios y destruir sólo la instancia desechable al terminar. El piloto INCIVSA y cualquier servicio o base real siguen bloqueados.

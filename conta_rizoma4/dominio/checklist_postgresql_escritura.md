# Checklist de activación de escritura PostgreSQL

## Requisitos previos

- DDL 005 revisado y aprobado.
- Migración reversible probada.
- Repositorio de lectura validado.
- Repositorio en memoria utilizado como referencia.
- Correspondencias heredadas completas.
- Asientos sin hecho identificado marcados como NO_DETERMINADO.
- Actor y competencia formalizados.
- Transacciones append-only validadas.
- Rectificaciones enlazadas con originales.
- Hash de eventos independiente de autenticidad.

## Pruebas obligatorias

- Crear hecho en PostgreSQL.
- Crear evidencia y relación.
- Crear interpretación alternativa.
- Adoptar decisión.
- Crear representación.
- Crear asiento técnico.
- Crear rectificación.
- Verificar cadena.
- Reconstruir por fecha epistémica.
- Rollback de transacción.
- Importación dual.
- Verificación de diferencias.
- Revisión por empresa.
- Fallback al repositorio heredado.
- Bloqueo de UPDATE/DELETE histórico.
- Bloqueo de modificación no autorizada.

## Condiciones de bloqueo

No activar escritura si:

- falta una correspondencia heredada;
- existe una representación sin decisión;
- existe una rectificación sin original;
- existe un evento sin actor;
- existen diferencias contables sin explicación;
- la reconstrucción difiere entre memoria y PostgreSQL;
- no existe rollback probado;
- no existe identidad verificable;
- no existe modo legado reversible;
- no existe aprobación formal del responsable.

## Estrategia de activación

1. despliegue de sólo lectura;
2. verificación dual;
3. creación de objetos nuevos por empresa;
4. activación temporal de escritura;
5. observación y reconciliación;
6. activación completa;
7. congelación del modelo heredado;
8. migración progresiva de CLI/API.

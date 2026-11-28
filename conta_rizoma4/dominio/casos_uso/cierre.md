# Cierre contable en memoria

`preparar_cierre_integral` recibe representaciones contables ya registradas del ejercicio y calcula:

- Regularización de cuentas 6 y 7 contra 129, a partir de saldos deudores/acreedores.
- Asiento de cierre propuesto para cuentas 1 a 5 y 129.
- Asiento de apertura propuesto, inverso del cierre.
- Identificadores de las representaciones fuente y resultado del ejercicio.

Las líneas se conservan en `CierreContable`; **son una hoja de trabajo, no asientos contabilizados**. El caso `cerrar_ejercicio` registra el cierre del estado del ejercicio solo cuando el ejercicio, las representaciones fuente, el actor y la autorización están en `NucleoEpistemicoContable` y coinciden con las precondiciones. La reapertura requiere autorización de competencia y alcance `REAPERTURA_EJERCICIO` y motivo. Ambos cambios quedan en el ledger; la reconstrucción histórica recupera el estado y cierres disponibles en una fecha epistemológica.

## Límites y decisiones pendientes

- La generación automática cubre cuentas de grupos 1 a 7. Cualquier otra cuenta detiene el cálculo hasta definir su tratamiento.
- No registra las líneas propuestas como representaciones contables ni crea automáticamente el ejercicio siguiente.
- La autorización técnica exige competencias `CIERRE_EJERCICIO` o `REAPERTURA_EJERCICIO` y alcance igual al identificador del ejercicio. El modelo actual no acredita por sí mismo la competencia jurídica del autorizador ni identifica al destinatario de la autorización; esa política requiere completarse antes de producción.
- Los casos de uso actuales de facturación, existencias, tesorería e inmovilizado consultan `EjercicioContable.permite_registro`: bloquean en `CERRADO` y admiten registro en `REABIERTO`. Los adaptadores externos aún deben aplicar la misma precondición.
- El cálculo no sustituye la revisión de regularizaciones, ajustes de cierre o criterios contables que no estén representados en el mayor proporcionado.

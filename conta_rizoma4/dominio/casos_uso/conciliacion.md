# Conciliación bancaria en memoria

`conciliar_movimiento` crea un vínculo propuesto 1:1 sin alterar la línea de extracto ni el movimiento económico. Solo acepta movimientos económicos en estado cobrado/pagado. Compara importes firmados: `COBRO` y `ANTICIPO_CLIENTE` son entradas; `PAGO` es salida. Los tipos sin una convención explícita generan error. Una diferencia produce estado `DIFERENCIA` y no se da por conciliada.

`resumir_conciliacion` recibe saldos iniciales y colecciones ya cargadas por quien lo invoca. Calcula los saldos finales, su diferencia y los elementos que siguen pendientes. Comprueba unicidad de IDs, existencia y coherencia de referencias, recalcula las diferencias y solo descuenta vínculos 1:1 exactos. No valida la autenticidad ni el periodo de esos snapshots.

Pendiente para un incremento posterior: persistencia/eventos en el núcleo de memoria, conciliación de una línea contra varias, comisiones y otros movimientos bancarios, importación de extractos y política de fechas/valoración. No se crean ajustes contables ni se determina el tratamiento legal o contable de diferencias.

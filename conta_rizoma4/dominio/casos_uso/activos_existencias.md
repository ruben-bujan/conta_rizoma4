# Inmovilizado y existencias en memoria

Las propuestas contables de alta/amortización y compra/venta se etiquetan PGC-PYMES y validan entidad, ejercicio y fecha. El llamante conserva la responsabilidad de elegir las cuentas.

`calcular_cuota_amortizacion_lineal` calcula una cuota por periodo a partir del coste, valor residual, vida útil y número de periodos ya amortizados. Reparte los céntimos restantes en los primeros periodos para que las cuotas acumuladas alcancen exactamente la base amortizable. No prescribe vida útil, fecha de inicio, método ni criterio de componentes.

`valorar_salida_existencias` acepta capas de entrada ordenadas cronológicamente por quien llama y una salida. Permite FIFO y promedio ponderado (PMP), ambos sobre coste histórico proporcionado; devuelve coste de salida y capas/coste restante. El resultado es una valoración de trabajo: no registra la salida, el asiento de variación de existencias ni deterioros.

Queda pendiente documentar por entidad la política de valoración y su aplicación consistente, gestionar entradas/salidas y reconstrucción histórica como eventos, prorratear amortización por fechas, bajas y deterioros/reversiones, y conectar salidas valoradas con asientos. No se infieren criterios normativos ni parámetros de activos concretos.

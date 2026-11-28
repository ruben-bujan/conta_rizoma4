\echo '===== 1. TABLAS PRESENTES ====='
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_type = 'BASE TABLE' AND table_schema NOT IN ('pg_catalog','information_schema')
ORDER BY 1,2;

\echo '===== 2. COLUMNAS DE asiento_contable / linea_asiento (orden físico) ====='
SELECT table_name, ordinal_position, column_name, data_type,
       character_maximum_length AS len, is_nullable, column_default
FROM information_schema.columns
WHERE table_name IN ('asiento_contable','linea_asiento')
ORDER BY table_name, ordinal_position;

\echo '===== 3. TODAS LAS RESTRICCIONES (nombres REALES) ====='
SELECT conrelid::regclass AS tabla,
       conname,
       contype,
       pg_get_constraintdef(oid) AS definicion,
       conkey AS columnas_locales
FROM pg_constraint
WHERE conrelid IN ('asiento_contable'::regclass, 'linea_asiento'::regclass)
ORDER BY conrelid::regclass::text, contype, conname;

\echo '===== 4. CLAVES FORANEAS QUE APUNTAN A asiento_contable ====='
SELECT c.conrelid::regclass  AS tabla_origen,
       c.conname,
       pg_get_constraintdef(c.oid) AS definicion
FROM pg_constraint c
WHERE c.confrelid = 'asiento_contable'::regclass AND c.contype = 'f';

\echo '===== 5. ÍNDICES ====='
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('asiento_contable','linea_asiento')
ORDER BY tablename, indexname;

\echo '===== 6. VOLUMETRIA ====='
SELECT 'asiento_contable' AS tabla, count(*) AS filas FROM asiento_contable
UNION ALL
SELECT 'linea_asiento', count(*) FROM linea_asiento;

\echo '===== 7. DISTRIBUCION POR EMPRESA ====='
SELECT empresa_id, count(*) AS asientos, min(indice) AS idx_min, max(indice) AS idx_max
FROM asiento_contable
GROUP BY empresa_id
ORDER BY empresa_id;

\echo '===== 8. ¿HAY INDICES REPETIDOS ENTRE EMPRESAS? (viabilidad PK compuesta) ====='
SELECT indice, count(DISTINCT empresa_id) AS empresas_que_lo_usan
FROM asiento_contable
GROUP BY indice
HAVING count(DISTINCT empresa_id) > 1
ORDER BY indice
LIMIT 20;

\echo '===== 9. ¿empresa_id NULOS O VACIOS? (bloquearian ADD PRIMARY KEY) ====='
SELECT count(*) AS filas_sin_empresa
FROM asiento_contable
WHERE empresa_id IS NULL OR btrim(empresa_id) = '';

\echo '===== 10. ¿LINEAS HUERFANAS O DESCUADRADAS? ====='
SELECT empresa_id, indice, total_debe, total_haber
FROM v_asiento_cuadre WHERE NOT cuadra LIMIT 20;
LEFT JOIN asiento_contable a
       ON a.indice = l.asiento_indice AND a.empresa_id = l.empresa_id
WHERE a.indice IS NULL
GROUP BY l.empresa_id, l.asiento_indice
LIMIT 20;

\echo '===== 11. ASIENTOS CON HASH VACIO (detecta reversiones incompletas) ====='
SELECT empresa_id, indice, fecha, left(concepto,60) AS concepto
FROM asiento_contable
WHERE hash IS NULL OR hash = ''
ORDER BY empresa_id, indice
LIMIT 20;
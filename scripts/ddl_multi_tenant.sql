-- =========================================================================
-- MIGRACIÓN MULTI-TENANT — CONTA-RIZOMA4 (Corrección H-02)
-- =========================================================================

-- Asegurar que la tabla de empresas existe y opera como nodo maestro
CREATE TABLE IF NOT EXISTS empresa_config (
    empresa_id VARCHAR(50) PRIMARY KEY,
    nombre_fiscal VARCHAR(255) NOT NULL,
    cif VARCHAR(20) NOT NULL,
    ejercicio INTEGER NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Migración segura de restricciones en entornos ya poblados
DO $$ 
BEGIN
    -- 1. Eliminar restricción de clave primaria simple anterior si existiera
DO $$
DECLARE
  pk_cols text[];
BEGIN
  SELECT array_agg(a.attname::text ORDER BY k.ord)
    INTO pk_cols
  FROM pg_constraint c
  CROSS JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord)
  JOIN pg_attribute a
    ON a.attrelid = c.conrelid AND a.attnum = k.attnum
  WHERE c.conrelid = 'asiento_contable'::regclass
    AND c.contype = 'p';

  IF pk_cols = ARRAY['empresa_id','indice'] THEN
    RAISE NOTICE 'PK ya compuesta (empresa_id, indice): no se toca, FK intactas.';
    RETURN;
  END IF;

  RAISE EXCEPTION
    'PK de asiento_contable es % — migración desde PK simple requiere recrear las FK. '
    'Aplica el bloque de recreación explícito.', pk_cols;
END $$;

    -- 2. Aplicar clave primaria compuesta definitiva
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'asiento_contable_pkey' 
        AND table_name = 'asiento_contable'
    ) THEN
        ALTER TABLE asiento_contable ADD CONSTRAINT asiento_contable_pkey PRIMARY KEY (empresa_id, indice);
    END IF;
END $$;

-- Índice optimizado para búsquedas rápidas por tenant y estado
CREATE INDEX IF NOT EXISTS idx_asiento_empresa_estado 
ON asiento_contable(empresa_id, estado);
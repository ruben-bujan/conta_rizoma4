-- Añadir empresa_id a las tablas de partida doble. Idempotente.

ALTER TABLE asiento_contable
    ADD COLUMN IF NOT EXISTS empresa_id VARCHAR(50) NOT NULL DEFAULT 'default';

ALTER TABLE linea_asiento
    ADD COLUMN IF NOT EXISTS empresa_id VARCHAR(50) NOT NULL DEFAULT 'default';

-- Eliminar UNIQUE global de indice (ya no es único global)
ALTER TABLE asiento_contable
    DROP CONSTRAINT IF EXISTS asiento_contable_indice_key;

-- Añadir UNIQUE compuesto (empresa_id, indice) si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'asiento_contable_empresa_indice_key'
    ) THEN
        ALTER TABLE asiento_contable
            ADD CONSTRAINT asiento_contable_empresa_indice_key
            UNIQUE (empresa_id, indice);
    END IF;
END $$;

-- Índices
CREATE INDEX IF NOT EXISTS idx_asiento_empresa
    ON asiento_contable(empresa_id, indice);
CREATE INDEX IF NOT EXISTS idx_asiento_empresa_fecha
    ON asiento_contable(empresa_id, fecha);
CREATE INDEX IF NOT EXISTS idx_linea_empresa
    ON linea_asiento(empresa_id, cuenta_pgc);
CREATE INDEX IF NOT EXISTS idx_linea_asiento_empresa
    ON linea_asiento(empresa_id, asiento_indice);

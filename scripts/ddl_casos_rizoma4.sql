-- BLOQUE 1: asociación explícita empresa CONTA ↔ caso investigador RIZOMA4.
-- Aplicar después de ddl_partida_doble.sql y ddl_custodia.sql.

-- Normaliza los nombres que declara ddl_partida_doble.sql con los que consume
-- el repositorio Python actual. Si ambas columnas existen, conserva el valor
-- ya presente en la columna de destino y relaja la antigua para permitir
-- nuevas inserciones exclusivamente con el contrato vigente.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'asiento_contable' AND column_name = 'hash_anterior'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'asiento_contable' AND column_name = 'hash_previo'
    ) THEN
        ALTER TABLE asiento_contable RENAME COLUMN hash_anterior TO hash_previo;
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'asiento_contable' AND column_name = 'hash_anterior'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'asiento_contable' AND column_name = 'hash_previo'
    ) THEN
        UPDATE asiento_contable SET hash_previo = COALESCE(hash_previo, hash_anterior);
        ALTER TABLE asiento_contable ALTER COLUMN hash_anterior DROP NOT NULL;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'asiento_contable' AND column_name = 'hash_actual'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'asiento_contable' AND column_name = 'hash'
    ) THEN
        ALTER TABLE asiento_contable RENAME COLUMN hash_actual TO hash;
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'asiento_contable' AND column_name = 'hash_actual'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'asiento_contable' AND column_name = 'hash'
    ) THEN
        UPDATE asiento_contable SET hash = COALESCE(hash, hash_actual);
        ALTER TABLE asiento_contable ALTER COLUMN hash_actual DROP NOT NULL;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'linea_asiento' AND column_name = 'descripcion'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'linea_asiento' AND column_name = 'concepto_linea'
    ) THEN
        ALTER TABLE linea_asiento RENAME COLUMN descripcion TO concepto_linea;
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'linea_asiento' AND column_name = 'descripcion'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'linea_asiento' AND column_name = 'concepto_linea'
    ) THEN
        UPDATE linea_asiento SET concepto_linea = COALESCE(concepto_linea, descripcion);
    END IF;
END $$;

ALTER TABLE asiento_contable
    ADD COLUMN IF NOT EXISTS metadatos JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS empresa_casos_rizoma4 (
    empresa_id       VARCHAR(50)  NOT NULL,
    caso_id          TEXT         NOT NULL,
    activo           BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_por       VARCHAR(128) NOT NULL,
    creado_en        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    modificado_por   VARCHAR(128) NOT NULL,
    modificado_en    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    desactivado_en   TIMESTAMPTZ,
    CONSTRAINT empresa_casos_rizoma4_pk PRIMARY KEY (empresa_id, caso_id),
    CONSTRAINT empresa_casos_rizoma4_caso_id_ck
        CHECK (caso_id ~ '^[A-Za-z0-9_-]+$')
);

CREATE INDEX IF NOT EXISTS idx_empresa_casos_rizoma4_activos
    ON empresa_casos_rizoma4 (empresa_id, activo, caso_id);

ALTER TABLE asiento_contable
    ADD COLUMN IF NOT EXISTS caso_id TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_asiento_empresa_caso_rizoma4'
          AND conrelid = 'asiento_contable'::regclass
    ) THEN
        ALTER TABLE asiento_contable
            ADD CONSTRAINT fk_asiento_empresa_caso_rizoma4
            FOREIGN KEY (empresa_id, caso_id)
            REFERENCES empresa_casos_rizoma4 (empresa_id, caso_id)
            ON UPDATE RESTRICT ON DELETE RESTRICT;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_asiento_empresa_caso_rizoma4
    ON asiento_contable (empresa_id, caso_id);

-- La comprobación en trigger evita una carrera entre la validación API y
-- la desactivación administrativa de la asociación.
CREATE OR REPLACE FUNCTION conta_validar_caso_rizoma4_activo()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.caso_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM empresa_casos_rizoma4
        WHERE empresa_id = NEW.empresa_id
          AND caso_id = NEW.caso_id
          AND (
              activo = TRUE
              OR COALESCE((NEW.metadatos->>'es_reversion')::BOOLEAN, FALSE) = TRUE
          )
    ) THEN
        RAISE EXCEPTION
            'Caso RIZOMA4 % no está asociado y activo para empresa %',
            NEW.caso_id, NEW.empresa_id
            USING ERRCODE = '23503';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_asiento_caso_rizoma4_activo ON asiento_contable;
CREATE TRIGGER trg_asiento_caso_rizoma4_activo
    BEFORE INSERT OR UPDATE OF caso_id, empresa_id ON asiento_contable
    FOR EACH ROW EXECUTE FUNCTION conta_validar_caso_rizoma4_activo();

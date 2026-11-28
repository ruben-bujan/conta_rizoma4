-- M2: ALTER fuera del runtime. Idempotente.
ALTER TABLE pgc_jerarquia ADD COLUMN IF NOT EXISTS grupo INTEGER;
ALTER TABLE pgc_jerarquia
    ADD COLUMN IF NOT EXISTS tipo_registro VARCHAR(20) NOT NULL DEFAULT 'cuenta';
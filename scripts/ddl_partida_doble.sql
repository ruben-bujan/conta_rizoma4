CREATE TABLE IF NOT EXISTS asiento_contable (
    indice        INTEGER PRIMARY KEY,
    fecha         DATE NOT NULL,
    concepto      TEXT NOT NULL,
    hash_previo   VARCHAR(64) NOT NULL,
    hash          VARCHAR(64) NOT NULL,
    metadatos     JSONB DEFAULT '{}'::jsonb,
    creado_en     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_asiento_fecha ON asiento_contable(fecha);
CREATE INDEX IF NOT EXISTS idx_asiento_hash ON asiento_contable(hash);

CREATE TABLE IF NOT EXISTS linea_asiento (
    id              BIGSERIAL PRIMARY KEY,
    asiento_indice  INTEGER NOT NULL REFERENCES asiento_contable(indice) ON DELETE CASCADE,
    cuenta_pgc      VARCHAR(20) NOT NULL,
    debe_centimos   BIGINT NOT NULL DEFAULT 0,
    haber_centimos  BIGINT NOT NULL DEFAULT 0,
    parrafo_pgc_id  INTEGER,
    concepto_linea  TEXT,
    metadatos       JSONB DEFAULT '{}'::jsonb,
    CHECK (debe_centimos >= 0 AND haber_centimos >= 0),
    CHECK ((debe_centimos > 0 AND haber_centimos = 0) OR (haber_centimos > 0 AND debe_centimos = 0))
);
CREATE INDEX IF NOT EXISTS idx_linea_asiento ON linea_asiento(asiento_indice);
CREATE INDEX IF NOT EXISTS idx_linea_cuenta ON linea_asiento(cuenta_pgc);

CREATE OR REPLACE VIEW v_asiento_cuadre AS
SELECT asiento_indice,
       SUM(debe_centimos) AS total_debe,
       SUM(haber_centimos) AS total_haber,
       SUM(debe_centimos) - SUM(haber_centimos) AS descuadre
FROM linea_asiento
GROUP BY asiento_indice;

-- Lote de incorporación INCIVSA: conserva origen y separa datos fuente de
-- propuestas contables. Aplicar dentro de la transacción del importador.
CREATE TABLE IF NOT EXISTS incivsa_lote_importacion (
    lote_id CHAR(64) PRIMARY KEY,
    empresa_id VARCHAR(50) NOT NULL,
    fuente VARCHAR(255) NOT NULL,
    sha256_fuente CHAR(64) NOT NULL,
    version_parser VARCHAR(40) NOT NULL,
    total_grupos INTEGER NOT NULL CHECK (total_grupos >= 0),
    total_filas_origen INTEGER NOT NULL CHECK (total_filas_origen >= 0),
    grupos_propuestos INTEGER NOT NULL CHECK (grupos_propuestos >= 0),
    grupos_no_determinados INTEGER NOT NULL CHECK (grupos_no_determinados >= 0),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (empresa_id, sha256_fuente)
);

CREATE TABLE IF NOT EXISTS incivsa_grupo_origen (
    lote_id CHAR(64) NOT NULL REFERENCES incivsa_lote_importacion(lote_id),
    empresa_id VARCHAR(50) NOT NULL,
    clave_origen_sha256 CHAR(64) NOT NULL,
    codigo_origen TEXT NOT NULL,
    fecha_origen TEXT NOT NULL,
    estado_migracion VARCHAR(60) NOT NULL CHECK (
        estado_migracion IN (
            'PROPUESTA_BORRADOR',
            'NO_DETERMINADO_PRECISION_O_LINEA',
            'NO_DETERMINADO_FECHA',
            'NO_DETERMINADO_DESCUADRE'
        )
    ),
    filas_origen JSONB NOT NULL,
    lineas_propuestas JSONB NOT NULL DEFAULT '[]'::jsonb,
    error_origen VARCHAR(80),
    asiento_indice BIGINT,
    PRIMARY KEY (lote_id, clave_origen_sha256),
    UNIQUE (lote_id, asiento_indice),
    UNIQUE (empresa_id, clave_origen_sha256),
    FOREIGN KEY (empresa_id, asiento_indice)
        REFERENCES asiento_contable(empresa_id, indice)
);

CREATE INDEX IF NOT EXISTS idx_incivsa_grupo_estado
    ON incivsa_grupo_origen(lote_id, estado_migracion);

CREATE TABLE IF NOT EXISTS incivsa_lote_evento (
    evento_id BIGSERIAL PRIMARY KEY,
    lote_id CHAR(64) NOT NULL REFERENCES incivsa_lote_importacion(lote_id),
    tipo VARCHAR(60) NOT NULL,
    descripcion TEXT NOT NULL,
    cantidad_afectada INTEGER NOT NULL CHECK (cantidad_afectada >= 0),
    hash_anterior CHAR(64),
    hash_resultante CHAR(64),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION incivsa_bloquear_mutacion_origen()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'El lote de origen INCIVSA es append-only'
        USING ERRCODE = '42501';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_incivsa_lote_inmutable ON incivsa_lote_importacion;
CREATE TRIGGER trg_incivsa_lote_inmutable
    BEFORE UPDATE OR DELETE ON incivsa_lote_importacion
    FOR EACH ROW EXECUTE FUNCTION incivsa_bloquear_mutacion_origen();

DROP TRIGGER IF EXISTS trg_incivsa_lote_truncate ON incivsa_lote_importacion;
CREATE TRIGGER trg_incivsa_lote_truncate
    BEFORE TRUNCATE ON incivsa_lote_importacion
    FOR EACH STATEMENT EXECUTE FUNCTION incivsa_bloquear_mutacion_origen();

DROP TRIGGER IF EXISTS trg_incivsa_grupo_inmutable ON incivsa_grupo_origen;
CREATE TRIGGER trg_incivsa_grupo_inmutable
    BEFORE UPDATE OR DELETE ON incivsa_grupo_origen
    FOR EACH ROW EXECUTE FUNCTION incivsa_bloquear_mutacion_origen();

DROP TRIGGER IF EXISTS trg_incivsa_grupo_truncate ON incivsa_grupo_origen;
CREATE TRIGGER trg_incivsa_grupo_truncate
    BEFORE TRUNCATE ON incivsa_grupo_origen
    FOR EACH STATEMENT EXECUTE FUNCTION incivsa_bloquear_mutacion_origen();

DROP TRIGGER IF EXISTS trg_incivsa_evento_inmutable ON incivsa_lote_evento;
CREATE TRIGGER trg_incivsa_evento_inmutable
    BEFORE UPDATE OR DELETE ON incivsa_lote_evento
    FOR EACH ROW EXECUTE FUNCTION incivsa_bloquear_mutacion_origen();

DROP TRIGGER IF EXISTS trg_incivsa_evento_truncate ON incivsa_lote_evento;
CREATE TRIGGER trg_incivsa_evento_truncate
    BEFORE TRUNCATE ON incivsa_lote_evento
    FOR EACH STATEMENT EXECUTE FUNCTION incivsa_bloquear_mutacion_origen();

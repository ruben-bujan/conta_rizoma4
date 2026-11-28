-- =========================================================================
-- DDL PARTIDA DOBLE - CONTA-RIZOMA4 (Esquema Multi-Tenant Nativo)
-- =========================================================================

CREATE TABLE IF NOT EXISTS asiento_contable (
    empresa_id VARCHAR(50) NOT NULL,
    indice BIGINT NOT NULL,
    fecha DATE NOT NULL,
    concepto TEXT NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'BORRADOR',
    documento_ref VARCHAR(255) NULL,
    hash_anterior VARCHAR(64) NOT NULL,
    hash_actual VARCHAR(64) NOT NULL,
    creado_en TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- CLAVE PRIMARIA COMPUESTA: Permite aislar índices por tenant (H-02)
    CONSTRAINT asiento_contable_pkey PRIMARY KEY (empresa_id, indice)
);

CREATE TABLE IF NOT EXISTS linea_asiento (
    id SERIAL PRIMARY KEY,
    empresa_id VARCHAR(50) NOT NULL,
    asiento_indice BIGINT NOT NULL,
    cuenta_pgc VARCHAR(10) NOT NULL,
    debe_centimos BIGINT NOT NULL DEFAULT 0,
    haber_centimos BIGINT NOT NULL DEFAULT 0,
    parrafo_pgc_id INTEGER NULL,
    descripcion TEXT NULL,

    -- CLAVE FORÁNEA COMPUESTA: Asegura integridad referencial por tenant
    CONSTRAINT fk_linea_asiento_cabecera 
        FOREIGN KEY (empresa_id, asiento_indice) 
        REFERENCES asiento_contable(empresa_id, indice) 
        ON DELETE CASCADE
);

-- Vista de control de cuadre por asiento y empresa
CREATE OR REPLACE VIEW v_asiento_cuadre AS
SELECT 
    c.empresa_id,
    c.indice,
    c.fecha,
    c.estado,
    COALESCE(SUM(l.debe_centimos), 0) AS total_debe,
    COALESCE(SUM(l.haber_centimos), 0) AS total_haber,
(COALESCE(SUM(l.debe_centimos), 0) = COALESCE(SUM(l.haber_centimos), 0)) AS cuadra,
(COALESCE(SUM(l.debe_centimos), 0) - COALESCE(SUM(l.haber_centimos), 0)) AS descuadre,
c.indice AS asiento_indice
FROM asiento_contable c
LEFT JOIN linea_asiento l ON c.empresa_id = l.empresa_id AND c.indice = l.asiento_indice
GROUP BY c.empresa_id, c.indice, c.fecha, c.estado;

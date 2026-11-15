-- Consolidación de grupo clásico. Idempotente.

-- 1. Relaciones de participación (matriz → filial)
CREATE TABLE IF NOT EXISTS relaciones_grupo (
    matriz_id       VARCHAR(50) NOT NULL,
    filial_id       VARCHAR(50) NOT NULL,
    porcentaje      NUMERIC(5,2) NOT NULL CHECK (porcentaje > 0 AND porcentaje <= 100),
    fecha_inicio    DATE NOT NULL,
    fecha_fin       DATE,
    PRIMARY KEY (matriz_id, filial_id, fecha_inicio)
);
CREATE INDEX IF NOT EXISTS idx_rel_matriz ON relaciones_grupo(matriz_id);
CREATE INDEX IF NOT EXISTS idx_rel_filial ON relaciones_grupo(filial_id);

-- 2. Eliminaciones intragrupo (propuestas por el motor, validadas por humano)
CREATE TABLE IF NOT EXISTS eliminaciones_propuestas (
    id              BIGSERIAL PRIMARY KEY,
    grupo_id        VARCHAR(50) NOT NULL,
    fecha_cierre    DATE NOT NULL,
    empresa_a       VARCHAR(50) NOT NULL,
    empresa_b       VARCHAR(50) NOT NULL,
    cuenta_a        VARCHAR(20) NOT NULL,
    cuenta_b        VARCHAR(20) NOT NULL,
    importe_centimos BIGINT NOT NULL,
    estado          VARCHAR(20) NOT NULL DEFAULT 'pendiente',
        -- pendiente | validada | rechazada
    validada_por    VARCHAR(100),
    validada_en     TIMESTAMPTZ,
    metadatos       JSONB DEFAULT '{}'::jsonb,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_elim_grupo ON eliminaciones_propuestas(grupo_id, fecha_cierre);
CREATE INDEX IF NOT EXISTS idx_elim_estado ON eliminaciones_propuestas(estado);

-- 3. Balances consolidados (cache materializada)
CREATE TABLE IF NOT EXISTS balances_consolidados (
    id              BIGSERIAL PRIMARY KEY,
    grupo_id        VARCHAR(50) NOT NULL,
    fecha_cierre    DATE NOT NULL,
    tipo            VARCHAR(20) NOT NULL,  -- 'balance' | 'pyg'
    datos           JSONB NOT NULL,
    version         INTEGER NOT NULL DEFAULT 1,
    generado_en     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (grupo_id, fecha_cierre, tipo, version)
);
CREATE INDEX IF NOT EXISTS idx_bal_grupo ON balances_consolidados(grupo_id, fecha_cierre);

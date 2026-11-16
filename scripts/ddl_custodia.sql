-- Fase 4b: leases, obras, operarios, documentos, estados de asiento.

-- 1. Obras
CREATE TABLE IF NOT EXISTS obras (
    obra_id       VARCHAR(50) PRIMARY KEY,
    empresa_id    VARCHAR(50) NOT NULL,
    nombre        VARCHAR(255) NOT NULL,
    cliente_nif   VARCHAR(20),
    presupuesto_centimos BIGINT,
    fecha_inicio  DATE,
    fecha_fin     DATE,
    estado        VARCHAR(20) DEFAULT 'activa',
    config_sync   JSONB DEFAULT '{}'::jsonb,
    creado_en     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_obras_empresa ON obras(empresa_id);

-- 2. Operarios
CREATE TABLE IF NOT EXISTS operarios (
    operario_id   VARCHAR(50) PRIMARY KEY,
    empresa_id    VARCHAR(50) NOT NULL,
    nombre        VARCHAR(255) NOT NULL,
    rol           VARCHAR(20) NOT NULL,
    email         VARCHAR(255),
    certificado   TEXT,
    activo        BOOLEAN DEFAULT TRUE,
    creado_en     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_operarios_empresa ON operarios(empresa_id);
CREATE INDEX IF NOT EXISTS idx_operarios_rol ON operarios(empresa_id, rol);

-- 3. Leases
CREATE TABLE IF NOT EXISTS leases (
    lease_id          VARCHAR(64) PRIMARY KEY,
    empresa_id        VARCHAR(50) NOT NULL,
    obra_id           VARCHAR(50) REFERENCES obras(obra_id),
    tipo              VARCHAR(20) NOT NULL DEFAULT 'asiento',
    indice_reservado  INTEGER NOT NULL,
    operario          VARCHAR(50) NOT NULL,
    estado            VARCHAR(20) NOT NULL DEFAULT 'CONCEDIDO',
    creado_en         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expira_en         TIMESTAMPTZ NOT NULL,
    renovado_en       TIMESTAMPTZ,
    usado_en          TIMESTAMPTZ,
    UNIQUE (empresa_id, indice_reservado)
);
CREATE INDEX IF NOT EXISTS idx_leases_estado ON leases(empresa_id, estado);
CREATE INDEX IF NOT EXISTS idx_leases_expira ON leases(expira_en) WHERE estado = 'CONCEDIDO';

-- 4. Documentos (referencia al CAS de rizoma4)
CREATE TABLE IF NOT EXISTS documentos (
    id            BIGSERIAL PRIMARY KEY,
    empresa_id    VARCHAR(50) NOT NULL,
    obra_id       VARCHAR(50) REFERENCES obras(obra_id),
    hash_cas      VARCHAR(64) NOT NULL,
    tipo          VARCHAR(50) NOT NULL,
    nombre        VARCHAR(255),
    tamano_bytes  BIGINT,
    subido_por    VARCHAR(50),
    subido_en     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (empresa_id, hash_cas)
);

-- 5. Asientos: añadir campos de custodia
ALTER TABLE asiento_contable
    ADD COLUMN IF NOT EXISTS obra_id VARCHAR(50) REFERENCES obras(obra_id),
    ADD COLUMN IF NOT EXISTS operario_creador VARCHAR(50),
    ADD COLUMN IF NOT EXISTS operario_visador VARCHAR(50),
    ADD COLUMN IF NOT EXISTS operario_aprobador VARCHAR(50),
    ADD COLUMN IF NOT EXISTS lease_id VARCHAR(64) REFERENCES leases(lease_id),
    ADD COLUMN IF NOT EXISTS estado VARCHAR(20) NOT NULL DEFAULT 'BORRADOR',
    ADD COLUMN IF NOT EXISTS documento_ref VARCHAR(64),
    ADD COLUMN IF NOT EXISTS alerta TEXT;

CREATE INDEX IF NOT EXISTS idx_asiento_estado ON asiento_contable(empresa_id, estado);
CREATE INDEX IF NOT EXISTS idx_asiento_obra ON asiento_contable(empresa_id, obra_id);

-- 6. Relación asiento ↔ documentos (N:M)
CREATE TABLE IF NOT EXISTS asiento_documentos (
    empresa_id      VARCHAR(50) NOT NULL,
    asiento_indice  INTEGER NOT NULL,
    documento_id    BIGINT REFERENCES documentos(id),
    PRIMARY KEY (empresa_id, asiento_indice, documento_id),
    FOREIGN KEY (empresa_id, asiento_indice)
        REFERENCES asiento_contable(empresa_id, indice) ON DELETE CASCADE
);

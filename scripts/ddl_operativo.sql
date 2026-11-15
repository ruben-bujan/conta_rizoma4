-- DDL de las tablas operativas de conta-rizoma4 (Ciclo 3 + 5).
-- Idempotente: se puede aplicar varias veces.

CREATE TABLE IF NOT EXISTS acto_economico (
    id              BIGSERIAL PRIMARY KEY,
    indice          INTEGER NOT NULL UNIQUE,
    fecha           DATE NOT NULL,
    cuenta_pgc      VARCHAR(20) NOT NULL,
    importe_centimos BIGINT NOT NULL,
    moneda          VARCHAR(3) NOT NULL DEFAULT 'EUR',
    concepto        TEXT NOT NULL,
    actividad_nivel VARCHAR(20),
    actividad_id    INTEGER,
    interlocutor_tipo VARCHAR(20),
    interlocutor_nif  VARCHAR(20),
    documento_tipo    VARCHAR(50),
    documento_ref     VARCHAR(100),
    parrafo_pgc_id    INTEGER,
    creado_por        VARCHAR(100) NOT NULL,
    validado_por      VARCHAR(100),
    aprobado_por      VARCHAR(100),
    huella_contenido  VARCHAR(64) NOT NULL,
    hash_previo       VARCHAR(64) NOT NULL,
    hash              VARCHAR(64) NOT NULL,
    metadatos         JSONB DEFAULT '{}'::jsonb,
    creado_en         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Columnas de enlace (Ciclo 5): idempotentes para BDs existentes.
ALTER TABLE acto_economico
    ADD COLUMN IF NOT EXISTS justificacion_indice INTEGER;
ALTER TABLE acto_economico
    ADD COLUMN IF NOT EXISTS cuenta_contrapartida VARCHAR(20);

CREATE INDEX IF NOT EXISTS idx_acto_fecha  ON acto_economico(fecha);
CREATE INDEX IF NOT EXISTS idx_acto_cuenta ON acto_economico(cuenta_pgc);
CREATE INDEX IF NOT EXISTS idx_acto_hash   ON acto_economico(hash);
CREATE INDEX IF NOT EXISTS idx_acto_justificacion
    ON acto_economico(justificacion_indice);

CREATE TABLE IF NOT EXISTS justificacion_interna (
    id              BIGSERIAL PRIMARY KEY,
    indice          INTEGER NOT NULL UNIQUE,
    fecha           DATE NOT NULL,
    cuenta_pgc      VARCHAR(20) NOT NULL,
    importe_centimos BIGINT NOT NULL,
    concepto        TEXT NOT NULL,
    obra_ref        VARCHAR(100),
    contrato_ref    VARCHAR(100),
    creado_por      VARCHAR(100) NOT NULL,
    validado_por    VARCHAR(100),
    huella_contenido VARCHAR(64) NOT NULL,
    hash_previo     VARCHAR(64) NOT NULL,
    hash            VARCHAR(64) NOT NULL,
    metadatos       JSONB DEFAULT '{}'::jsonb,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_just_obra ON justificacion_interna(obra_ref);
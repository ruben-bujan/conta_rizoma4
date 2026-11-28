-- Migración DDL 005: estructura mínima persistente del dominio epistemológico-contable.
-- Artefacto de diseño. NO EJECUTAR hasta completar pruebas de migración reversible.
-- Depende de: scripts/ddl_partida_doble.sql y scripts/ddl_custodia.sql.

CREATE TABLE IF NOT EXISTS dominio_entidad (
    entidad_id VARCHAR(100) PRIMARY KEY,
    nombre TEXT NOT NULL,
    moneda VARCHAR(3) NOT NULL DEFAULT 'EUR',
    metadatos JSONB NOT NULL DEFAULT '{}'::jsonb,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dominio_actor (
    actor_id VARCHAR(100) PRIMARY KEY,
    nombre TEXT NOT NULL,
    tipo VARCHAR(30) NOT NULL DEFAULT 'HUMANO',
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    metadatos JSONB NOT NULL DEFAULT '{}'::jsonb,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dominio_hecho (
    entidad_id VARCHAR(100) NOT NULL,
    hecho_id VARCHAR(100) NOT NULL,
    tipo VARCHAR(100) NOT NULL,
    descripcion TEXT NOT NULL,
    estado_economico VARCHAR(50) NOT NULL,
    estado_epistemologico VARCHAR(50) NOT NULL,
    ocurrido_inicio TIMESTAMPTZ,
    ocurrido_fin TIMESTAMPTZ,
    precision_temporal VARCHAR(30) NOT NULL DEFAULT 'DESCONOCIDA',
    conocido_en TIMESTAMPTZ,
    registrado_en TIMESTAMPTZ NOT NULL,
    incertidumbre JSONB,
    magnitudes JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadatos JSONB NOT NULL DEFAULT '{}'::jsonb,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (entidad_id, hecho_id),
    FOREIGN KEY (entidad_id) REFERENCES dominio_entidad(entidad_id)
);

CREATE TABLE IF NOT EXISTS dominio_relacion_hecho (
    entidad_id VARCHAR(100) NOT NULL,
    origen_hecho_id VARCHAR(100) NOT NULL,
    destino_hecho_id VARCHAR(100) NOT NULL,
    relacion VARCHAR(50) NOT NULL,
    registrado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor_id VARCHAR(100),
    motivo TEXT,
    PRIMARY KEY (entidad_id, origen_hecho_id, destino_hecho_id, relacion),
    FOREIGN KEY (entidad_id, origen_hecho_id)
        REFERENCES dominio_hecho(entidad_id, hecho_id),
    FOREIGN KEY (entidad_id, destino_hecho_id)
        REFERENCES dominio_hecho(entidad_id, hecho_id)
);

CREATE TABLE IF NOT EXISTS dominio_fuente (
    fuente_id VARCHAR(100) PRIMARY KEY,
    tipo VARCHAR(50) NOT NULL,
    identidad TEXT NOT NULL,
    competencia TEXT,
    metadatos JSONB NOT NULL DEFAULT '{}'::jsonb,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dominio_evidencia (
    evidencia_id VARCHAR(100) PRIMARY KEY,
    fuente_id VARCHAR(100) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    referencia TEXT NOT NULL,
    recibida_en TIMESTAMPTZ NOT NULL,
    integridad VARCHAR(50) NOT NULL DEFAULT 'NO_VERIFICADA',
    autenticidad VARCHAR(50) NOT NULL DEFAULT 'NO_VALORADA',
    veracidad VARCHAR(50) NOT NULL DEFAULT 'NO_VALORADA',
    calidad VARCHAR(50) NOT NULL DEFAULT 'NO_VALORADA',
    metadatos JSONB NOT NULL DEFAULT '{}'::jsonb,
    FOREIGN KEY (fuente_id) REFERENCES dominio_fuente(fuente_id)
);

CREATE TABLE IF NOT EXISTS dominio_relacion_evidencia_hecho (
    entidad_id VARCHAR(100) NOT NULL,
    hecho_id VARCHAR(100) NOT NULL,
    evidencia_id VARCHAR(100) NOT NULL,
    relacion VARCHAR(50) NOT NULL,
    fundamento TEXT NOT NULL,
    valorado_en TIMESTAMPTZ NOT NULL,
    actor_id VARCHAR(100),
    PRIMARY KEY (entidad_id, hecho_id, evidencia_id, relacion),
    FOREIGN KEY (entidad_id, hecho_id)
        REFERENCES dominio_hecho(entidad_id, hecho_id),
    FOREIGN KEY (evidencia_id) REFERENCES dominio_evidencia(evidencia_id)
);

CREATE TABLE IF NOT EXISTS dominio_criterio (
    criterio_id VARCHAR(100) PRIMARY KEY,
    categoria VARCHAR(50) NOT NULL,
    nombre TEXT NOT NULL,
    fundamento TEXT NOT NULL,
    version VARCHAR(50) NOT NULL,
    vigente_desde TIMESTAMPTZ NOT NULL,
    vigente_hasta TIMESTAMPTZ,
    metadatos JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (criterio_id, version)
);

CREATE TABLE IF NOT EXISTS dominio_interpretacion (
    entidad_id VARCHAR(100) NOT NULL,
    interpretacion_id VARCHAR(100) NOT NULL,
    hecho_id VARCHAR(100) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    descripcion TEXT NOT NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'PROPUESTA',
    propuesta_por VARCHAR(100) NOT NULL,
    propuesta_en TIMESTAMPTZ NOT NULL,
    incertidumbre JSONB,
    metadatos JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (entidad_id, interpretacion_id),
    FOREIGN KEY (entidad_id, hecho_id)
        REFERENCES dominio_hecho(entidad_id, hecho_id)
);

CREATE TABLE IF NOT EXISTS dominio_interpretacion_evidencia (
    entidad_id VARCHAR(100) NOT NULL,
    interpretacion_id VARCHAR(100) NOT NULL,
    evidencia_id VARCHAR(100) NOT NULL,
    PRIMARY KEY (entidad_id, interpretacion_id, evidencia_id),
    FOREIGN KEY (entidad_id, interpretacion_id)
        REFERENCES dominio_interpretacion(entidad_id, interpretacion_id),
    FOREIGN KEY (evidencia_id) REFERENCES dominio_evidencia(evidencia_id)
);

CREATE TABLE IF NOT EXISTS dominio_interpretacion_criterio (
    entidad_id VARCHAR(100) NOT NULL,
    interpretacion_id VARCHAR(100) NOT NULL,
    criterio_id VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    PRIMARY KEY (entidad_id, interpretacion_id, criterio_id, version),
    FOREIGN KEY (entidad_id, interpretacion_id)
        REFERENCES dominio_interpretacion(entidad_id, interpretacion_id),
    FOREIGN KEY (criterio_id, version)
        REFERENCES dominio_criterio(criterio_id, version)
);

CREATE TABLE IF NOT EXISTS dominio_autorizacion (
    entidad_id VARCHAR(100) NOT NULL,
    autorizacion_id VARCHAR(100) NOT NULL,
    actor_id VARCHAR(100) NOT NULL,
    competencia TEXT NOT NULL,
    alcance TEXT NOT NULL,
    otorgada_en TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (entidad_id, autorizacion_id)
);

CREATE TABLE IF NOT EXISTS dominio_decision (
    entidad_id VARCHAR(100) NOT NULL,
    decision_id VARCHAR(100) NOT NULL,
    objeto_id VARCHAR(100) NOT NULL,
    interpretacion_adoptada_id VARCHAR(100) NOT NULL,
    motivo TEXT NOT NULL,
    actor_id VARCHAR(100) NOT NULL,
    autorizacion_id VARCHAR(100),
    decidida_en TIMESTAMPTZ NOT NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'PROPUESTA',
    metadatos JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (entidad_id, decision_id),
    FOREIGN KEY (entidad_id, interpretacion_adoptada_id)
        REFERENCES dominio_interpretacion(entidad_id, interpretacion_id),
    FOREIGN KEY (entidad_id, autorizacion_id)
        REFERENCES dominio_autorizacion(entidad_id, autorizacion_id)
);

CREATE TABLE IF NOT EXISTS dominio_representacion (
    entidad_id VARCHAR(100) NOT NULL,
    representacion_id VARCHAR(100) NOT NULL,
    interpretacion_id VARCHAR(100) NOT NULL,
    decision_id VARCHAR(100) NOT NULL,
    marco VARCHAR(50) NOT NULL,
    fecha_contable DATE NOT NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'PROPUESTA',
    metadatos JSONB NOT NULL DEFAULT '{}'::jsonb,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (entidad_id, representacion_id),
    FOREIGN KEY (entidad_id, interpretacion_id)
        REFERENCES dominio_interpretacion(entidad_id, interpretacion_id),
    FOREIGN KEY (entidad_id, decision_id)
        REFERENCES dominio_decision(entidad_id, decision_id)
);

CREATE TABLE IF NOT EXISTS dominio_representacion_hecho (
    entidad_id VARCHAR(100) NOT NULL,
    representacion_id VARCHAR(100) NOT NULL,
    hecho_id VARCHAR(100) NOT NULL,
    relacion VARCHAR(50) NOT NULL DEFAULT 'RECONOCE',
    PRIMARY KEY (entidad_id, representacion_id, hecho_id),
    FOREIGN KEY (entidad_id, representacion_id)
        REFERENCES dominio_representacion(entidad_id, representacion_id),
    FOREIGN KEY (entidad_id, hecho_id)
        REFERENCES dominio_hecho(entidad_id, hecho_id)
);

CREATE TABLE IF NOT EXISTS dominio_linea_representacion (
    entidad_id VARCHAR(100) NOT NULL,
    representacion_id VARCHAR(100) NOT NULL,
    linea_id BIGSERIAL NOT NULL,
    cuenta VARCHAR(20) NOT NULL,
    debe_centimos BIGINT NOT NULL DEFAULT 0,
    haber_centimos BIGINT NOT NULL DEFAULT 0,
    concepto TEXT,
    PRIMARY KEY (entidad_id, representacion_id, linea_id),
    FOREIGN KEY (entidad_id, representacion_id)
        REFERENCES dominio_representacion(entidad_id, representacion_id)
);

CREATE TABLE IF NOT EXISTS dominio_rectificacion (
    entidad_id VARCHAR(100) NOT NULL,
    rectificacion_id VARCHAR(100) NOT NULL,
    representacion_original_id VARCHAR(100) NOT NULL,
    representacion_nueva_id VARCHAR(100) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    causa TEXT NOT NULL,
    motivo TEXT NOT NULL,
    actor_id VARCHAR(100) NOT NULL,
    autorizacion_id VARCHAR(100),
    creada_en TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (entidad_id, rectificacion_id),
    FOREIGN KEY (entidad_id, representacion_original_id)
        REFERENCES dominio_representacion(entidad_id, representacion_id),
    FOREIGN KEY (entidad_id, representacion_nueva_id)
        REFERENCES dominio_representacion(entidad_id, representacion_id)
);

CREATE TABLE IF NOT EXISTS dominio_evento (
    entidad_id VARCHAR(100) NOT NULL,
    evento_id VARCHAR(100) NOT NULL,
    indice BIGINT NOT NULL,
    tipo VARCHAR(100) NOT NULL,
    objeto_tipo VARCHAR(50) NOT NULL,
    objeto_id VARCHAR(100) NOT NULL,
    actor_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    estado_anterior JSONB,
    estado_posterior JSONB,
    motivo TEXT,
    referencias JSONB NOT NULL DEFAULT '[]'::jsonb,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    huella VARCHAR(64) NOT NULL,
    hash_previo VARCHAR(64) NOT NULL,
    hash VARCHAR(64) NOT NULL,
    PRIMARY KEY (entidad_id, evento_id),
    UNIQUE (entidad_id, indice)
);

CREATE TABLE IF NOT EXISTS dominio_instantanea (
    entidad_id VARCHAR(100) NOT NULL,
    instantanea_id VARCHAR(100) NOT NULL,
    fecha_epistemica TIMESTAMPTZ NOT NULL,
    fecha_economica TIMESTAMPTZ,
    datos JSONB NOT NULL,
    hash VARCHAR(64) NOT NULL,
    creada_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (entidad_id, instantanea_id)
);

CREATE TABLE IF NOT EXISTS dominio_correspondencia_heredada (
    entidad_id VARCHAR(100) NOT NULL,
    origen_tipo VARCHAR(100) NOT NULL,
    origen_indice BIGINT,
    destino_tipo VARCHAR(100) NOT NULL,
    destino_id VARCHAR(100) NOT NULL,
    estado_migracion VARCHAR(100) NOT NULL,
    observaciones JSONB NOT NULL DEFAULT '[]'::jsonb,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (entidad_id, origen_tipo, origen_indice, destino_tipo, destino_id)
);

CREATE INDEX IF NOT EXISTS idx_dominio_hecho_estado
    ON dominio_hecho(entidad_id, estado_epistemologico);
CREATE INDEX IF NOT EXISTS idx_dominio_evidencia_recibida
    ON dominio_evidencia(recibida_en);
CREATE INDEX IF NOT EXISTS idx_dominio_decision_fecha
    ON dominio_decision(entidad_id, decidida_en);
CREATE INDEX IF NOT EXISTS idx_dominio_evento_timestamp
    ON dominio_evento(entidad_id, timestamp, indice);
CREATE INDEX IF NOT EXISTS idx_dominio_representacion_fecha
    ON dominio_representacion(entidad_id, fecha_contable);

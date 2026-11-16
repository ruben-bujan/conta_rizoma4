-- Corpus forense: sujetos, expedientes, flujos, danos.

-- 1. Sujetos (MIPYME o persona física)
CREATE TABLE IF NOT EXISTS sujetos (
    sujeto_id        VARCHAR(50) PRIMARY KEY,
    tipo             VARCHAR(20) NOT NULL,  -- "MIPYME" | "FISICA"
    nombre           VARCHAR(255) NOT NULL,
    nif              VARCHAR(20),
    sector           VARCHAR(50),
    anonimizado      BOOLEAN DEFAULT TRUE,
    metadatos        JSONB DEFAULT '{}'::jsonb,
    creado_en        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sujetos_tipo ON sujetos(tipo);
CREATE INDEX IF NOT EXISTS idx_sujetos_sector ON sujetos(sector);

-- 2. Expedientes (1 por víctima)
CREATE TABLE IF NOT EXISTS expedientes (
    expediente_id    VARCHAR(50) PRIMARY KEY,
    sujeto_id        VARCHAR(50) NOT NULL REFERENCES sujetos(sujeto_id),
    contrato_publico_ref VARCHAR(100),
    tipo_contrato    VARCHAR(30),  -- "concesion" | "obras" | "suministros"
    fecha_inicio     DATE,
    fecha_fin        DATE,

    -- Vía de entrada a U1
    via_u1           VARCHAR(5),  -- "V1" | "V2" | "V3" | NULL
    es_punta_de_lanza BOOLEAN DEFAULT FALSE,

    -- Concurso
    estado_concurso  VARCHAR(20) DEFAULT 'ninguno',  -- presentado|presumido|caido|recaydo|ninguno
    fecha_concurso   DATE,
    fecha_conclusion DATE,
    seccion_sexta    BOOLEAN DEFAULT FALSE,
    calificacion     VARCHAR(20),  -- fortuito|culpable|sin_calificar
    incidente_concursal_por_no_diligencia BOOLEAN DEFAULT FALSE,

    -- Buena fe
    buena_fe_acreditada BOOLEAN DEFAULT FALSE,
    medio_prueba_buena_fe VARCHAR(30),  -- testimonio|documentos|indicios|combinacion

    -- Relevancia del menoscabo (R4)
    nivel_vida_antes_centimos   BIGINT,
    nivel_vida_despues_centimos BIGINT,
    porcentaje_menoscabo        NUMERIC(5,2),
    quiebra_modo_vida           BOOLEAN DEFAULT FALSE,

    -- Clasificación (calculada)
    universo         VARCHAR(10),  -- U1 | U2 | U3 | no_victima
    tipo_reparacion  VARCHAR(50),

    metadatos        JSONB DEFAULT '{}'::jsonb,
    creado_en        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_exp_sujeto ON expedientes(sujeto_id);
CREATE INDEX IF NOT EXISTS idx_exp_universo ON expedientes(universo);
CREATE INDEX IF NOT EXISTS idx_exp_estado_concurso ON expedientes(estado_concurso);

-- 3. Flujos (N por expediente)
CREATE TABLE IF NOT EXISTS flujos (
    id              BIGSERIAL PRIMARY KEY,
    expediente_id   VARCHAR(50) NOT NULL REFERENCES expedientes(expediente_id),
    fecha           DATE NOT NULL,
    concepto        TEXT NOT NULL,
    importe_centimos BIGINT NOT NULL,  -- + ingreso, - gasto
    categoria       VARCHAR(30) NOT NULL,  -- factura|requerimiento|renuncia_interes|cobro_principal|cobro_interes
    documento_ref   VARCHAR(64),
    hash_previo     VARCHAR(64) NOT NULL DEFAULT '0000000000000000000000000000000000000000000000000000000000000000',
    hash            VARCHAR(64) NOT NULL,
    metadatos       JSONB DEFAULT '{}'::jsonb,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_flujo_expediente ON flujos(expediente_id);

-- 4. Daños (1 por expediente)
CREATE TABLE IF NOT EXISTS danos (
    id              BIGSERIAL PRIMARY KEY,
    expediente_id   VARCHAR(50) NOT NULL UNIQUE REFERENCES expedientes(expediente_id),
    principal_debido_centimos        BIGINT NOT NULL,
    interes_renunciado_centimos      BIGINT NOT NULL,
    interes_compuesto_centimos       BIGINT NOT NULL,
    dano_moral_centimos              BIGINT NOT NULL DEFAULT 0,
    consecuencias_indirectas_centimos BIGINT NOT NULL DEFAULT 0,
    dano_total_centimos              BIGINT NOT NULL,
    fecha_corte      DATE NOT NULL,
    calculado_en     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--
-- PostgreSQL database dump
--

\restrict c1Wz8bKI9a8q6hQicvhHZaRP1pHOqcjCRCggxZy8dB6a5KFJclVB0TS4B1v6Uyn

-- Dumped from database version 15.19 (Debian 15.19-1.pgdg13+2)
-- Dumped by pg_dump version 15.19 (Debian 15.19-1.pgdg13+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: actualizar_version_nodo(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.actualizar_version_nodo() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.version := OLD.version + 1;
    NEW.timestamp_ultima_modif := NOW();
    RETURN NEW;
END;
$$;


--
-- Name: bloquear_modificacion_registro(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.bloquear_modificacion_registro() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    RAISE EXCEPTION 'I1 VIOLADO: El registro de trazabilidad es INMUTABLE. Operación % prohibida.', TG_OP;
    RETURN NULL;
END;
$$;


--
-- Name: fn_verificar_integridad_caso(character varying); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_verificar_integridad_caso(p_caso character varying) RETURNS TABLE(integro boolean, primer_asiento_corrupto bigint, total_asientos bigint, sello_actual character)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_integro BOOLEAN := TRUE;
    v_corrupto BIGINT := NULL;
    v_total BIGINT;
    v_sello CHAR(64);
    v_previo CHAR(64);
    r RECORD;
BEGIN
    SELECT COUNT(*) INTO v_total FROM registro_trazabilidad WHERE caso_id = p_caso;
    SELECT hash_asiento INTO v_sello FROM registro_trazabilidad WHERE caso_id = p_caso ORDER BY id DESC LIMIT 1;
    v_previo := '0000000000000000000000000000000000000000000000000000000000000000';
    FOR r IN SELECT * FROM registro_trazabilidad WHERE caso_id = p_caso ORDER BY id LOOP
        IF r.hash_previo != v_previo THEN
            v_integro := FALSE;
            v_corrupto := r.id;
            EXIT;
        END IF;
        v_previo := r.hash_asiento;
    END LOOP;
    RETURN QUERY SELECT v_integro, v_corrupto, v_total, v_sello;
END;
$$;


--
-- Name: validar_cadena_hash(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.validar_cadena_hash() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    ultimo_hash CHAR(64);
    hash_calculado CHAR(64);
BEGIN
    SELECT hash_asiento INTO ultimo_hash
    FROM registro_trazabilidad
    WHERE caso_id = NEW.caso_id
    ORDER BY id DESC
    LIMIT 1;
    
    IF ultimo_hash IS NULL THEN
        IF NEW.hash_previo IS NOT NULL 
           AND NEW.hash_previo != '0000000000000000000000000000000000000000000000000000000000000000' THEN
            RAISE EXCEPTION 'I1 VIOLADO: Primer asiento debe tener hash_previo nulo o ceros';
        END IF;
    ELSE
        IF NEW.hash_previo != ultimo_hash THEN
            RAISE EXCEPTION 'I1 VIOLADO: hash_previo no coincide con el último asiento del caso %', NEW.caso_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: anclajes_externos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.anclajes_externos (
    id bigint NOT NULL,
    caso_id character varying(64) NOT NULL,
    tipo_anclaje character varying(30) NOT NULL,
    rango_asientos int8range NOT NULL,
    raiz_merkle character(64),
    token_rfc3161 bytea,
    tsa_url character varying(500),
    tx_hash_externo character varying(128),
    fecha_anclaje timestamp with time zone DEFAULT now() NOT NULL,
    verificado boolean DEFAULT false NOT NULL
);


--
-- Name: anclajes_externos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.anclajes_externos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: anclajes_externos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.anclajes_externos_id_seq OWNED BY public.anclajes_externos.id;


--
-- Name: casos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.casos (
    id text NOT NULL,
    titulo text NOT NULL,
    descripcion text NOT NULL,
    dominio text NOT NULL,
    subdominio text NOT NULL,
    estado text NOT NULL,
    timestamp_creacion timestamp with time zone DEFAULT now() NOT NULL,
    timestamp_actualizacion timestamp with time zone DEFAULT now() NOT NULL,
    metadatos jsonb DEFAULT '{}'::jsonb NOT NULL,
    CONSTRAINT chk_estado_caso CHECK ((estado = ANY (ARRAY['ACTIVO'::text, 'PAUSADO'::text, 'CERRADO'::text, 'ARCHIVADO'::text])))
);


--
-- Name: condiciones_contorno; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.condiciones_contorno (
    id character varying(64) NOT NULL,
    caso_id character varying(64) NOT NULL,
    nodo_primigenio_id character varying(64) NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    estado character varying(24) DEFAULT 'PROPUESTA'::character varying NOT NULL,
    dominio character varying(64) NOT NULL,
    subdominio character varying(64) NOT NULL,
    causa_problema jsonb DEFAULT '{}'::jsonb NOT NULL,
    identidad_promotora jsonb DEFAULT '{}'::jsonb NOT NULL,
    restricciones jsonb DEFAULT '{}'::jsonb NOT NULL,
    origen_expediente_id character varying(64),
    hash_contenido character(64) NOT NULL,
    timestamp_creacion timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_contorno_estado CHECK (((estado)::text = ANY ((ARRAY['PROPUESTA'::character varying, 'VALIDADA'::character varying, 'SUPERADA'::character varying])::text[])))
);


--
-- Name: diferenciales; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.diferenciales (
    id character varying(64) NOT NULL,
    caso_id character varying(64) NOT NULL,
    tipo character varying(32) NOT NULL,
    fuente_nodo_id character varying(64),
    descripcion text NOT NULL,
    fuerza numeric(4,3) DEFAULT 1.000,
    hipotesis_incompatibles text[] DEFAULT '{}'::text[],
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: expedientes_ejecucion; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.expedientes_ejecucion (
    id character varying(64) NOT NULL,
    caso_id character varying(64) NOT NULL,
    directorio_relativo text NOT NULL,
    manifiesto_sha256 character(64) NOT NULL,
    entrada_sha256 character(64),
    pipeline_sha256 character(64),
    version_pipeline character varying(64),
    turnos_entrada integer,
    metaturnos_resultantes integer,
    timestamp_inicio timestamp with time zone,
    timestamp_fin timestamp with time zone,
    metadatos jsonb DEFAULT '{}'::jsonb NOT NULL,
    timestamp_registro timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: hiperrelaciones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hiperrelaciones (
    id character varying(64) NOT NULL,
    tipo character varying(32) NOT NULL,
    origen_id character varying(64) NOT NULL,
    destino_id character varying(64) NOT NULL,
    metadatos jsonb DEFAULT '{}'::jsonb,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: hipotesis; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hipotesis (
    id character varying(64) NOT NULL,
    caso_id character varying(64) NOT NULL,
    descripcion text NOT NULL,
    peso numeric(5,3) DEFAULT 1.000,
    activa boolean DEFAULT true NOT NULL,
    eliminada_por character varying(64),
    fecha_eliminacion timestamp with time zone,
    motivo_eliminacion text,
    motivo_resurreccion text,
    nodos_soporte text[] DEFAULT '{}'::text[],
    timestamp_creacion timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: metaturno_turnos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.metaturno_turnos (
    id bigint NOT NULL,
    metaturno_id character varying(64) NOT NULL,
    secuencia integer NOT NULL,
    emisor character varying(16) NOT NULL,
    texto text NOT NULL,
    dominio character varying(32) NOT NULL,
    tipo_interaccion character varying(32) NOT NULL,
    timestamp_turno timestamp with time zone DEFAULT now() NOT NULL,
    turno_origen_id character varying(128),
    secuencia_origen integer,
    metadatos jsonb DEFAULT '{}'::jsonb NOT NULL
);


--
-- Name: metaturno_turnos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.metaturno_turnos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: metaturno_turnos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.metaturno_turnos_id_seq OWNED BY public.metaturno_turnos.id;


--
-- Name: metaturnos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.metaturnos (
    id character varying(64) NOT NULL,
    caso_id character varying(64) NOT NULL,
    dominio character varying(32) NOT NULL,
    turno_inicial text DEFAULT ''::text NOT NULL,
    turno_final text,
    estado character varying(16) DEFAULT 'ACTIVO'::character varying NOT NULL,
    timestamp_inicio timestamp with time zone DEFAULT now() NOT NULL,
    timestamp_fin timestamp with time zone,
    hash_auditoria character(64),
    expediente_id character varying(64),
    secuencia_origen integer,
    metadatos jsonb DEFAULT '{}'::jsonb NOT NULL,
    CONSTRAINT chk_estado_metaturno CHECK (((estado)::text = ANY ((ARRAY['ACTIVO'::character varying, 'CERRADO'::character varying])::text[])))
);


--
-- Name: nodos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nodos (
    id character varying(64) NOT NULL,
    tipo_fundamental character varying(16) NOT NULL,
    rol character varying(32) NOT NULL,
    ambito character varying(16) NOT NULL,
    origen_parte character varying(16) NOT NULL,
    dimension_restriccion jsonb DEFAULT '{}'::jsonb NOT NULL,
    dimension_empirica jsonb DEFAULT '{}'::jsonb NOT NULL,
    dimension_temporal jsonb DEFAULT '{}'::jsonb NOT NULL,
    padres character varying(64)[] DEFAULT '{}'::character varying[] NOT NULL,
    hijos character varying(64)[] DEFAULT '{}'::character varying[] NOT NULL,
    estado_ciclo character varying(16) DEFAULT 'INSTANCIADO'::character varying NOT NULL,
    estado_estabilizacion character varying(32),
    estado_eficacia character varying(16) DEFAULT 'ACTIVO'::character varying NOT NULL,
    patologia character varying(32),
    atributos_especiales character varying(30)[] DEFAULT '{}'::character varying[] NOT NULL,
    competencia text DEFAULT ''::text NOT NULL,
    peso_epistemico real DEFAULT 1.0 NOT NULL,
    plazo_contradiccion_seg bigint,
    fecha_publicacion timestamp with time zone,
    sellos character(64)[] DEFAULT '{}'::bpchar[] NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    timestamp_creacion timestamp with time zone DEFAULT now() NOT NULL,
    timestamp_ultima_modif timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_ambito CHECK (((ambito)::text = ANY ((ARRAY['GENERAL'::character varying, 'PARTICULAR'::character varying])::text[]))),
    CONSTRAINT chk_estado_ciclo CHECK (((estado_ciclo)::text = ANY ((ARRAY['INSTANCIADO'::character varying, 'TRAZADO'::character varying, 'PUBLICADO'::character varying, 'VALIDADO'::character varying, 'CERTIFICADO'::character varying, 'DOCTRINA'::character varying, 'FOSIL'::character varying])::text[]))),
    CONSTRAINT chk_origen CHECK (((origen_parte)::text = ANY ((ARRAY['PRIVADA'::character varying, 'PUBLICA'::character varying])::text[]))),
    CONSTRAINT chk_tipo_fundamental CHECK (((tipo_fundamental)::text = ANY ((ARRAY['PRIMIGENIO'::character varying, 'NOTARY'::character varying, 'BUILDER'::character varying, 'RECONSTRUCTOR'::character varying])::text[])))
);


--
-- Name: rechazos_ingesta; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rechazos_ingesta (
    id bigint NOT NULL,
    caso_id character varying(64) NOT NULL,
    entrada_cruda jsonb NOT NULL,
    errores text[] NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: rechazos_ingesta_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rechazos_ingesta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rechazos_ingesta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rechazos_ingesta_id_seq OWNED BY public.rechazos_ingesta.id;


--
-- Name: registro_trazabilidad; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.registro_trazabilidad (
    id bigint NOT NULL,
    caso_id character varying(64) NOT NULL,
    acto character varying(32) NOT NULL,
    nodo_id character varying(64),
    huella_contenido character(64) NOT NULL,
    hash_previo character(64),
    hash_asiento character(64) NOT NULL,
    metadatos jsonb DEFAULT '{}'::jsonb NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL,
    firma_digital text,
    key_id character varying(100),
    CONSTRAINT acto_valido CHECK (((acto)::text = ANY ((ARRAY['TRAZAR'::character varying, 'PUBLICAR'::character varying, 'VALIDAR'::character varying, 'CERTIFICAR'::character varying, 'DOCTRINA'::character varying, 'FOSILIZAR'::character varying, 'REVOCAR'::character varying, 'RECHAZO_INGESTA'::character varying, 'DELTA_K'::character varying, 'ALTERIDAD'::character varying, 'ALTERIDAD_BLOQUEADA'::character varying, 'ALTERIDAD_SUPERADA'::character varying, 'DEPRECAR_ACTOS_PROPIOS'::character varying, 'INTERPELACION'::character varying, 'ACTA_ITV'::character varying, 'ITV_RESUELTA'::character varying, 'CADENA_COMPETENCIA'::character varying, 'APERTURA'::character varying, 'CORROBORACION'::character varying, 'CONSTITUIR_PRIMIGENIO'::character varying, 'FIJAR_CONTORNO'::character varying, 'REGISTRAR_EXPEDIENTE'::character varying, 'INGERIR_TURNO'::character varying, 'INGRESAR_METATURNO'::character varying, 'PROPONER_ENLACE'::character varying])::text[])))
);


--
-- Name: registro_trazabilidad_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.registro_trazabilidad_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: registro_trazabilidad_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.registro_trazabilidad_id_seq OWNED BY public.registro_trazabilidad.id;


--
-- Name: restricciones_virtuales; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.restricciones_virtuales (
    id text NOT NULL,
    caso_id text NOT NULL,
    nodo_primigenio_id text NOT NULL,
    contorno_id text NOT NULL,
    tipo text NOT NULL,
    categoria text NOT NULL,
    estado text NOT NULL,
    version integer NOT NULL,
    fecha_validacion date NOT NULL,
    titulo text NOT NULL,
    formulacion text NOT NULL,
    alcance jsonb NOT NULL,
    obligaciones jsonb NOT NULL,
    prohibiciones jsonb NOT NULL,
    mecanismos_cumplimiento jsonb NOT NULL,
    efecto_espacio_soluciones jsonb NOT NULL,
    fuentes jsonb NOT NULL,
    validacion_promotor jsonb NOT NULL,
    huella_contenido text NOT NULL,
    expediente_id text NOT NULL,
    dominio text NOT NULL,
    subdominio text NOT NULL,
    timestamp_creacion timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_categoria_restriccion CHECK ((categoria = ANY (ARRAY['OBLIGACION'::text, 'PROHIBICION'::text, 'PRINCIPIO'::text, 'CRITERIO'::text]))),
    CONSTRAINT chk_estado_restriccion CHECK ((estado = ANY (ARRAY['PROPUESTA'::text, 'VALIDADA'::text, 'REVISADA'::text, 'DEROGADA'::text]))),
    CONSTRAINT chk_tipo_restriccion CHECK ((tipo = ANY (ARRAY['RESTRICCION_VIRTUAL'::text, 'OBLIGACION'::text, 'PROHIBICION'::text, 'PRINCIPIO'::text])))
);


--
-- Name: turnos_crudos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.turnos_crudos (
    id bigint NOT NULL,
    conversacion_id character varying(64) NOT NULL,
    mensaje_id character varying(64) NOT NULL,
    secuencia integer NOT NULL,
    emisor character varying(16) NOT NULL,
    texto text NOT NULL,
    timestamp_origen timestamp with time zone,
    metadatos jsonb DEFAULT '{}'::jsonb NOT NULL,
    timestamp_ingesta timestamp with time zone DEFAULT now() NOT NULL,
    expediente_id character varying(64),
    huella_contenido character(64)
);


--
-- Name: turnos_crudos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.turnos_crudos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: turnos_crudos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.turnos_crudos_id_seq OWNED BY public.turnos_crudos.id;


--
-- Name: v_auditoria_metaturnos; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_auditoria_metaturnos AS
SELECT
    NULL::character varying(64) AS id,
    NULL::character varying(64) AS caso_id,
    NULL::character varying(32) AS dominio,
    NULL::character varying(16) AS estado,
    NULL::text AS turno_inicial,
    NULL::text AS turno_final,
    NULL::timestamp with time zone AS timestamp_inicio,
    NULL::timestamp with time zone AS timestamp_fin,
    NULL::bigint AS total_turnos,
    NULL::bigint AS vibraciones,
    NULL::bigint AS inversiones,
    NULL::bigint AS aclaraciones,
    NULL::bigint AS refutaciones,
    NULL::bigint AS errores;


--
-- Name: v_cementerio; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_cementerio AS
 SELECT hipotesis.id,
    hipotesis.caso_id,
    hipotesis.descripcion,
    hipotesis.peso,
    hipotesis.activa,
    hipotesis.eliminada_por,
    hipotesis.fecha_eliminacion,
    hipotesis.motivo_eliminacion,
    hipotesis.motivo_resurreccion,
    hipotesis.nodos_soporte,
    hipotesis.timestamp_creacion
   FROM public.hipotesis
  WHERE (NOT hipotesis.activa);


--
-- Name: v_frente_operativo; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_frente_operativo AS
 SELECT nodos.id,
    nodos.tipo_fundamental,
    nodos.rol,
    nodos.ambito,
    nodos.origen_parte,
    nodos.dimension_restriccion,
    nodos.dimension_empirica,
    nodos.dimension_temporal,
    nodos.padres,
    nodos.hijos,
    nodos.estado_ciclo,
    nodos.estado_estabilizacion,
    nodos.estado_eficacia,
    nodos.patologia,
    nodos.atributos_especiales,
    nodos.competencia,
    nodos.peso_epistemico,
    nodos.plazo_contradiccion_seg,
    nodos.fecha_publicacion,
    nodos.sellos,
    nodos.version,
    nodos.timestamp_creacion,
    nodos.timestamp_ultima_modif
   FROM public.nodos
  WHERE (((nodos.estado_ciclo)::text = ANY ((ARRAY['INSTANCIADO'::character varying, 'TRAZADO'::character varying, 'PUBLICADO'::character varying])::text[])) AND (nodos.patologia IS NULL));


--
-- Name: v_nodos_cristalizados; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_nodos_cristalizados AS
 SELECT nodos.id,
    nodos.tipo_fundamental,
    nodos.rol,
    nodos.ambito,
    nodos.origen_parte,
    nodos.dimension_restriccion,
    nodos.dimension_empirica,
    nodos.dimension_temporal,
    nodos.padres,
    nodos.hijos,
    nodos.estado_ciclo,
    nodos.estado_estabilizacion,
    nodos.estado_eficacia,
    nodos.patologia,
    nodos.atributos_especiales,
    nodos.competencia,
    nodos.peso_epistemico,
    nodos.plazo_contradiccion_seg,
    nodos.fecha_publicacion,
    nodos.sellos,
    nodos.version,
    nodos.timestamp_creacion,
    nodos.timestamp_ultima_modif
   FROM public.nodos
  WHERE ((nodos.estado_ciclo)::text = ANY ((ARRAY['VALIDADO'::character varying, 'CERTIFICADO'::character varying, 'DOCTRINA'::character varying, 'FOSIL'::character varying])::text[]));


--
-- Name: anclajes_externos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anclajes_externos ALTER COLUMN id SET DEFAULT nextval('public.anclajes_externos_id_seq'::regclass);


--
-- Name: metaturno_turnos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metaturno_turnos ALTER COLUMN id SET DEFAULT nextval('public.metaturno_turnos_id_seq'::regclass);


--
-- Name: rechazos_ingesta id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rechazos_ingesta ALTER COLUMN id SET DEFAULT nextval('public.rechazos_ingesta_id_seq'::regclass);


--
-- Name: registro_trazabilidad id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.registro_trazabilidad ALTER COLUMN id SET DEFAULT nextval('public.registro_trazabilidad_id_seq'::regclass);


--
-- Name: turnos_crudos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.turnos_crudos ALTER COLUMN id SET DEFAULT nextval('public.turnos_crudos_id_seq'::regclass);


--
-- Name: anclajes_externos anclajes_externos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anclajes_externos
    ADD CONSTRAINT anclajes_externos_pkey PRIMARY KEY (id);


--
-- Name: casos casos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.casos
    ADD CONSTRAINT casos_pkey PRIMARY KEY (id);


--
-- Name: condiciones_contorno condiciones_contorno_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.condiciones_contorno
    ADD CONSTRAINT condiciones_contorno_pkey PRIMARY KEY (id);


--
-- Name: diferenciales diferenciales_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.diferenciales
    ADD CONSTRAINT diferenciales_pkey PRIMARY KEY (id);


--
-- Name: expedientes_ejecucion expedientes_ejecucion_caso_id_manifiesto_sha256_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expedientes_ejecucion
    ADD CONSTRAINT expedientes_ejecucion_caso_id_manifiesto_sha256_key UNIQUE (caso_id, manifiesto_sha256);


--
-- Name: expedientes_ejecucion expedientes_ejecucion_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expedientes_ejecucion
    ADD CONSTRAINT expedientes_ejecucion_pkey PRIMARY KEY (id);


--
-- Name: hiperrelaciones hiperrelaciones_origen_id_destino_id_tipo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hiperrelaciones
    ADD CONSTRAINT hiperrelaciones_origen_id_destino_id_tipo_key UNIQUE (origen_id, destino_id, tipo);


--
-- Name: hiperrelaciones hiperrelaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hiperrelaciones
    ADD CONSTRAINT hiperrelaciones_pkey PRIMARY KEY (id);


--
-- Name: hipotesis hipotesis_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hipotesis
    ADD CONSTRAINT hipotesis_pkey PRIMARY KEY (id);


--
-- Name: metaturno_turnos metaturno_turnos_metaturno_id_secuencia_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metaturno_turnos
    ADD CONSTRAINT metaturno_turnos_metaturno_id_secuencia_key UNIQUE (metaturno_id, secuencia);


--
-- Name: metaturno_turnos metaturno_turnos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metaturno_turnos
    ADD CONSTRAINT metaturno_turnos_pkey PRIMARY KEY (id);


--
-- Name: metaturnos metaturnos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metaturnos
    ADD CONSTRAINT metaturnos_pkey PRIMARY KEY (id);


--
-- Name: nodos nodos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nodos
    ADD CONSTRAINT nodos_pkey PRIMARY KEY (id);


--
-- Name: rechazos_ingesta rechazos_ingesta_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rechazos_ingesta
    ADD CONSTRAINT rechazos_ingesta_pkey PRIMARY KEY (id);


--
-- Name: registro_trazabilidad registro_trazabilidad_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.registro_trazabilidad
    ADD CONSTRAINT registro_trazabilidad_pkey PRIMARY KEY (id);


--
-- Name: restricciones_virtuales restricciones_virtuales_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restricciones_virtuales
    ADD CONSTRAINT restricciones_virtuales_pkey PRIMARY KEY (id);


--
-- Name: turnos_crudos turnos_crudos_conversacion_id_secuencia_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.turnos_crudos
    ADD CONSTRAINT turnos_crudos_conversacion_id_secuencia_key UNIQUE (conversacion_id, secuencia);


--
-- Name: turnos_crudos turnos_crudos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.turnos_crudos
    ADD CONSTRAINT turnos_crudos_pkey PRIMARY KEY (id);


--
-- Name: idx_casos_dominio; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_casos_dominio ON public.casos USING btree (dominio);


--
-- Name: idx_casos_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_casos_estado ON public.casos USING btree (estado);


--
-- Name: idx_casos_subdominio; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_casos_subdominio ON public.casos USING btree (subdominio);


--
-- Name: idx_contorno_caso; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_contorno_caso ON public.condiciones_contorno USING btree (caso_id);


--
-- Name: idx_contorno_primigenio; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_contorno_primigenio ON public.condiciones_contorno USING btree (nodo_primigenio_id);


--
-- Name: idx_expedientes_caso; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_expedientes_caso ON public.expedientes_ejecucion USING btree (caso_id);


--
-- Name: idx_hipotesis_activa; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hipotesis_activa ON public.hipotesis USING btree (activa) WHERE (activa = true);


--
-- Name: idx_metaturnos_caso; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_metaturnos_caso ON public.metaturnos USING btree (caso_id);


--
-- Name: idx_metaturnos_dominio; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_metaturnos_dominio ON public.metaturnos USING btree (dominio);


--
-- Name: idx_metaturnos_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_metaturnos_estado ON public.metaturnos USING btree (estado);


--
-- Name: idx_nodos_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nodos_estado ON public.nodos USING btree (estado_ciclo);


--
-- Name: idx_nodos_hijos; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nodos_hijos ON public.nodos USING gin (hijos);


--
-- Name: idx_nodos_padres; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nodos_padres ON public.nodos USING gin (padres);


--
-- Name: idx_registro_caso; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_registro_caso ON public.registro_trazabilidad USING btree (caso_id);


--
-- Name: idx_registro_nodo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_registro_nodo ON public.registro_trazabilidad USING btree (nodo_id);


--
-- Name: idx_restricciones_caso; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restricciones_caso ON public.restricciones_virtuales USING btree (caso_id);


--
-- Name: idx_restricciones_contorno; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restricciones_contorno ON public.restricciones_virtuales USING btree (contorno_id);


--
-- Name: idx_restricciones_expediente; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restricciones_expediente ON public.restricciones_virtuales USING btree (expediente_id);


--
-- Name: idx_restricciones_nodo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_restricciones_nodo ON public.restricciones_virtuales USING btree (nodo_primigenio_id);


--
-- Name: idx_turnos_crudos_conversacion; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_turnos_crudos_conversacion ON public.turnos_crudos USING btree (conversacion_id);


--
-- Name: idx_turnos_crudos_expediente; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_turnos_crudos_expediente ON public.turnos_crudos USING btree (expediente_id);


--
-- Name: idx_turnos_crudos_secuencia; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_turnos_crudos_secuencia ON public.turnos_crudos USING btree (conversacion_id, secuencia);


--
-- Name: idx_turnos_metaturno; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_turnos_metaturno ON public.metaturno_turnos USING btree (metaturno_id);


--
-- Name: uq_metaturno_expediente_secuencia; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_metaturno_expediente_secuencia ON public.metaturnos USING btree (expediente_id, secuencia_origen) WHERE (expediente_id IS NOT NULL);


--
-- Name: uq_turno_origen_por_metaturno; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_turno_origen_por_metaturno ON public.metaturno_turnos USING btree (metaturno_id, turno_origen_id) WHERE (turno_origen_id IS NOT NULL);


--
-- Name: v_auditoria_metaturnos _RETURN; Type: RULE; Schema: public; Owner: -
--

CREATE OR REPLACE VIEW public.v_auditoria_metaturnos AS
 SELECT m.id,
    m.caso_id,
    m.dominio,
    m.estado,
    m.turno_inicial,
    m.turno_final,
    m.timestamp_inicio,
    m.timestamp_fin,
    count(t.id) AS total_turnos,
    count(t.id) FILTER (WHERE ((t.tipo_interaccion)::text ~~ 'VIBRADO%'::text)) AS vibraciones,
    count(t.id) FILTER (WHERE ((t.tipo_interaccion)::text ~~ 'INVERSION%'::text)) AS inversiones,
    count(t.id) FILTER (WHERE ((t.tipo_interaccion)::text ~~ 'ACLARADO%'::text)) AS aclaraciones,
    count(t.id) FILTER (WHERE ((t.tipo_interaccion)::text ~~ 'REFUTADO%'::text)) AS refutaciones,
    count(t.id) FILTER (WHERE ((t.tipo_interaccion)::text ~~ 'ERROR%'::text)) AS errores
   FROM (public.metaturnos m
     LEFT JOIN public.metaturno_turnos t ON (((m.id)::text = (t.metaturno_id)::text)))
  GROUP BY m.id;


--
-- Name: registro_trazabilidad trg_bloquear_delete; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_bloquear_delete BEFORE DELETE ON public.registro_trazabilidad FOR EACH ROW EXECUTE FUNCTION public.bloquear_modificacion_registro();


--
-- Name: registro_trazabilidad trg_bloquear_truncate; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_bloquear_truncate BEFORE TRUNCATE ON public.registro_trazabilidad FOR EACH STATEMENT EXECUTE FUNCTION public.bloquear_modificacion_registro();


--
-- Name: registro_trazabilidad trg_bloquear_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_bloquear_update BEFORE UPDATE ON public.registro_trazabilidad FOR EACH ROW EXECUTE FUNCTION public.bloquear_modificacion_registro();


--
-- Name: registro_trazabilidad trg_validar_hash_antes_insert; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_validar_hash_antes_insert BEFORE INSERT ON public.registro_trazabilidad FOR EACH ROW EXECUTE FUNCTION public.validar_cadena_hash();


--
-- Name: nodos trg_version_nodo; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_version_nodo BEFORE UPDATE ON public.nodos FOR EACH ROW EXECUTE FUNCTION public.actualizar_version_nodo();


--
-- Name: condiciones_contorno condiciones_contorno_nodo_primigenio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.condiciones_contorno
    ADD CONSTRAINT condiciones_contorno_nodo_primigenio_id_fkey FOREIGN KEY (nodo_primigenio_id) REFERENCES public.nodos(id);


--
-- Name: condiciones_contorno condiciones_contorno_origen_expediente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.condiciones_contorno
    ADD CONSTRAINT condiciones_contorno_origen_expediente_id_fkey FOREIGN KEY (origen_expediente_id) REFERENCES public.expedientes_ejecucion(id);


--
-- Name: diferenciales diferenciales_fuente_nodo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.diferenciales
    ADD CONSTRAINT diferenciales_fuente_nodo_id_fkey FOREIGN KEY (fuente_nodo_id) REFERENCES public.nodos(id);


--
-- Name: restricciones_virtuales fk_restricciones_caso; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restricciones_virtuales
    ADD CONSTRAINT fk_restricciones_caso FOREIGN KEY (caso_id) REFERENCES public.casos(id) ON DELETE RESTRICT;


--
-- Name: restricciones_virtuales fk_restricciones_contorno; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restricciones_virtuales
    ADD CONSTRAINT fk_restricciones_contorno FOREIGN KEY (contorno_id) REFERENCES public.condiciones_contorno(id) ON DELETE RESTRICT;


--
-- Name: restricciones_virtuales fk_restricciones_expediente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restricciones_virtuales
    ADD CONSTRAINT fk_restricciones_expediente FOREIGN KEY (expediente_id) REFERENCES public.expedientes_ejecucion(id) ON DELETE RESTRICT;


--
-- Name: restricciones_virtuales fk_restricciones_nodo; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.restricciones_virtuales
    ADD CONSTRAINT fk_restricciones_nodo FOREIGN KEY (nodo_primigenio_id) REFERENCES public.nodos(id) ON DELETE RESTRICT;


--
-- Name: hiperrelaciones hiperrelaciones_destino_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hiperrelaciones
    ADD CONSTRAINT hiperrelaciones_destino_id_fkey FOREIGN KEY (destino_id) REFERENCES public.nodos(id) ON DELETE CASCADE;


--
-- Name: hiperrelaciones hiperrelaciones_origen_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hiperrelaciones
    ADD CONSTRAINT hiperrelaciones_origen_id_fkey FOREIGN KEY (origen_id) REFERENCES public.nodos(id) ON DELETE CASCADE;


--
-- Name: metaturno_turnos metaturno_turnos_metaturno_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metaturno_turnos
    ADD CONSTRAINT metaturno_turnos_metaturno_id_fkey FOREIGN KEY (metaturno_id) REFERENCES public.metaturnos(id) ON DELETE CASCADE;


--
-- Name: metaturnos metaturnos_expediente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metaturnos
    ADD CONSTRAINT metaturnos_expediente_id_fkey FOREIGN KEY (expediente_id) REFERENCES public.expedientes_ejecucion(id);


--
-- Name: turnos_crudos turnos_crudos_expediente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.turnos_crudos
    ADD CONSTRAINT turnos_crudos_expediente_id_fkey FOREIGN KEY (expediente_id) REFERENCES public.expedientes_ejecucion(id);


--
-- PostgreSQL database dump complete
--

\unrestrict c1Wz8bKI9a8q6hQicvhHZaRP1pHOqcjCRCggxZy8dB6a5KFJclVB0TS4B1v6Uyn


-- 004_inmutabilidad.sql
-- Aplicar DESPUÉS de ddl_casos_rizoma4.sql (ese script hace UPDATE de
-- hash_previo/hash y quedaría bloqueado por este trigger).

-- ── 1. Rol de mantenimiento. NOLOGIN: nadie conecta con él directamente;
--       se activa con SET ROLE desde una credencial autorizada y nominativa.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'conta_mantenimiento') THEN
    CREATE ROLE conta_mantenimiento NOLOGIN;
  END IF;
END $$;

-- ── 2. Registro append-only de intervenciones de mantenimiento.
--       Es la "debida anotación en los sistemas mismos" (LGT 29.2.j).
CREATE TABLE IF NOT EXISTS conta_log_mantenimiento (
  id           BIGSERIAL PRIMARY KEY,
  ocurrido_en  TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
  rol_bd       TEXT NOT NULL,
  rol_sesion   TEXT NOT NULL,
  tabla        TEXT NOT NULL,
  operacion    TEXT NOT NULL,
  empresa_id   TEXT,
  indice       BIGINT,
  hash_afectado TEXT,
  motivo       TEXT NOT NULL
);

-- ── 3. Función de guarda. SECURITY INVOKER (por defecto): no eleva privilegios.
CREATE OR REPLACE FUNCTION conta_guarda_inmutabilidad()
RETURNS TRIGGER AS $$
DECLARE
  v_empresa TEXT;
  v_indice  BIGINT;
  v_hash    TEXT;
  v_motivo  TEXT;
BEGIN
  IF TG_OP = 'TRUNCATE' THEN
    IF NOT pg_has_role(current_user, 'conta_mantenimiento', 'USAGE') THEN
      RAISE EXCEPTION 'TRUNCATE prohibido sobre %: registro contable inmutable', TG_TABLE_NAME
        USING ERRCODE = '42501';
    END IF;
    RETURN NULL;
  END IF;

  IF TG_TABLE_NAME = 'asiento_contable' THEN
    v_empresa := OLD.empresa_id; v_indice := OLD.indice; v_hash := OLD.hash;
  ELSE
    v_empresa := OLD.empresa_id; v_indice := OLD.asiento_indice; v_hash := NULL;
  END IF;

  -- UPDATE: sólo se bloquea si cambia alguna columna que entra en la huella.
  IF TG_OP = 'UPDATE' THEN
    IF TG_TABLE_NAME = 'asiento_contable' THEN
      IF NEW.fecha          IS DISTINCT FROM OLD.fecha
      OR NEW.concepto       IS DISTINCT FROM OLD.concepto
      OR NEW.hash_previo    IS DISTINCT FROM OLD.hash_previo
      OR NEW.hash           IS DISTINCT FROM OLD.hash
      OR NEW.metadatos      IS DISTINCT FROM OLD.metadatos
      OR NEW.empresa_id     IS DISTINCT FROM OLD.empresa_id
      OR NEW.indice         IS DISTINCT FROM OLD.indice
      THEN
        NULL;  -- continúa hacia el bloqueo
      ELSE
        RETURN NEW;  -- sólo cambian columnas de workflow: permitido
      END IF;
    ELSE
      IF NEW.cuenta_pgc     IS DISTINCT FROM OLD.cuenta_pgc
      OR NEW.debe_centimos  IS DISTINCT FROM OLD.debe_centimos
      OR NEW.haber_centimos IS DISTINCT FROM OLD.haber_centimos
      OR NEW.parrafo_pgc_id IS DISTINCT FROM OLD.parrafo_pgc_id
      OR NEW.concepto_linea IS DISTINCT FROM OLD.concepto_linea
      OR NEW.empresa_id     IS DISTINCT FROM OLD.empresa_id
      OR NEW.asiento_indice IS DISTINCT FROM OLD.asiento_indice
      OR NEW.id             IS DISTINCT FROM OLD.id
      THEN
        NULL;
      ELSE
        RETURN NEW;
      END IF;
    END IF;
  END IF;

  -- Aquí sólo se llega si la operación toca contenido inmutable.
  IF NOT pg_has_role(current_user, 'conta_mantenimiento', 'USAGE') THEN
    RAISE EXCEPTION
      '% sobre %.% (empresa=%, indice=%) prohibido: usa reversión append-only',
      TG_OP, TG_TABLE_NAME, v_indice, v_empresa, v_indice
      USING ERRCODE = '42501';
  END IF;

  -- Vía de mantenimiento: exige motivo explícito y lo registra.
  v_motivo := current_setting('conta.motivo_mantenimiento', true);
  IF v_motivo IS NULL OR length(btrim(v_motivo)) < 10 THEN
    RAISE EXCEPTION
      'Mantenimiento requiere motivo: SET LOCAL conta.motivo_mantenimiento = ''...'' (>=10 caracteres)'
      USING ERRCODE = '23514';
  END IF;

  INSERT INTO conta_log_mantenimiento
    (rol_bd, rol_sesion, tabla, operacion, empresa_id, indice, hash_afectado, motivo)
  VALUES
    (current_user, session_user, TG_TABLE_NAME, TG_OP, v_empresa, v_indice, v_hash, v_motivo);

  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ── 4. Triggers
DROP TRIGGER IF EXISTS trg_inmutabilidad_asiento ON asiento_contable;
CREATE TRIGGER trg_inmutabilidad_asiento
  BEFORE DELETE OR UPDATE ON asiento_contable
  FOR EACH ROW EXECUTE FUNCTION conta_guarda_inmutabilidad();

DROP TRIGGER IF EXISTS trg_inmutabilidad_linea ON linea_asiento;
CREATE TRIGGER trg_inmutabilidad_linea
  BEFORE DELETE OR UPDATE ON linea_asiento
  FOR EACH ROW EXECUTE FUNCTION conta_guarda_inmutabilidad();

-- TRUNCATE no dispara triggers de fila: necesita trigger de sentencia.
DROP TRIGGER IF EXISTS trg_inmutabilidad_asiento_trunc ON asiento_contable;
CREATE TRIGGER trg_inmutabilidad_asiento_trunc
  BEFORE TRUNCATE ON asiento_contable
  FOR EACH STATEMENT EXECUTE FUNCTION conta_guarda_inmutabilidad();

DROP TRIGGER IF EXISTS trg_inmutabilidad_linea_trunc ON linea_asiento;
CREATE TRIGGER trg_inmutabilidad_linea_trunc
  BEFORE TRUNCATE ON linea_asiento
  FOR EACH STATEMENT EXECUTE FUNCTION conta_guarda_inmutabilidad();

-- ── 5. El log de mantenimiento es inmutable para todos, sin excepción de rol.
CREATE OR REPLACE FUNCTION conta_bloquea_log()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'conta_log_mantenimiento es append-only (%)', TG_OP
    USING ERRCODE = '42501';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_log_inmutable ON conta_log_mantenimiento;
CREATE TRIGGER trg_log_inmutable
  BEFORE UPDATE OR DELETE OR TRUNCATE ON conta_log_mantenimiento
  FOR EACH STATEMENT EXECUTE FUNCTION conta_bloquea_log();

GRANT INSERT, SELECT ON conta_log_mantenimiento TO conta_mantenimiento;
GRANT USAGE, SELECT ON SEQUENCE conta_log_mantenimiento_id_seq TO conta_mantenimiento;
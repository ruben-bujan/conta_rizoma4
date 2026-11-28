-- Usuario worker para importadores. Password DEBE setearse externamente:
--   psql -c "ALTER ROLE worker_rizoma4 PASSWORD '<nueva>';"
-- NUNCA commitear la password en claro.
CREATE ROLE worker_rizoma4 LOGIN PASSWORD 'CHANGE_ME_VIA_ALTER_ROLE'
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
GRANT CONNECT ON DATABASE conta_rizoma4 TO worker_rizoma4;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO worker_rizoma4;
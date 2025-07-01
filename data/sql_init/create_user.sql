CREATE USER ds_user WITH PASSWORD 'ds_password';

-- Схемы уже созданы в других файлах, поэтому используем IF NOT EXISTS
CREATE SCHEMA IF NOT EXISTS DS;

GRANT USAGE ON SCHEMA DS TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA DS TO postgres;

CREATE USER log_user WITH PASSWORD 'log_pass';

-- Схемы уже созданы в других файлах, поэтому используем IF NOT EXISTS
CREATE SCHEMA IF NOT EXISTS LOGS;

GRANT USAGE ON SCHEMA LOGS TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA LOGS TO postgres;
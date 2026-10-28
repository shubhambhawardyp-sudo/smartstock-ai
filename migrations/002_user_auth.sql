-- Run once on an existing smartstock_db created before login support.
-- New databases already receive these columns from schema.sql.
USE smartstock_db;

ALTER TABLE users
    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN last_login_at DATETIME NULL;

-- OpsDesk AI — PostgreSQL initialization
-- Runs once on first container startup

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- for full-text search

-- Verify
SELECT version();

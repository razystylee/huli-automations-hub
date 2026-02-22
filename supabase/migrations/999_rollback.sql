-- Migration: 999_rollback.sql
-- Description: Rollback all schema changes (for emergency/testing only)
-- Date: 2026-02-21
-- WARNING: This is DESTRUCTIVE - Use only if you need to start fresh

-- ============================================================================
-- ROLLBACK PLAN
-- ============================================================================

-- Step 1: Disable RLS (allow cleanup)
ALTER TABLE job_executions DISABLE ROW LEVEL SECURITY;
ALTER TABLE facebook_ads_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE hotmart_data DISABLE ROW LEVEL SECURITY;

-- Step 2: Drop all indices (tables will be dropped, but explicit for clarity)
DROP INDEX IF EXISTS idx_job_executions_job_id;
DROP INDEX IF EXISTS idx_job_executions_executed_at;
DROP INDEX IF EXISTS idx_job_executions_status;
DROP INDEX IF EXISTS idx_job_executions_job_status_date;

DROP INDEX IF EXISTS idx_facebook_ads_account_date;
DROP INDEX IF EXISTS idx_facebook_ads_campaign_date;
DROP INDEX IF EXISTS idx_facebook_ads_date;

DROP INDEX IF EXISTS idx_hotmart_sale_date;
DROP INDEX IF EXISTS idx_hotmart_producer_date;
DROP INDEX IF EXISTS idx_hotmart_product_date;
DROP INDEX IF EXISTS idx_hotmart_transaction_id;

DROP INDEX IF EXISTS idx_api_health_api_name_date;
DROP INDEX IF EXISTS idx_api_health_status;

-- Step 3: Drop partitions (order matters - partitions first)
DROP TABLE IF EXISTS job_executions_2016 CASCADE;
DROP TABLE IF EXISTS job_executions_2017 CASCADE;
DROP TABLE IF EXISTS job_executions_2018 CASCADE;
DROP TABLE IF EXISTS job_executions_2019 CASCADE;
DROP TABLE IF EXISTS job_executions_2020 CASCADE;
DROP TABLE IF EXISTS job_executions_2021 CASCADE;
DROP TABLE IF EXISTS job_executions_2022 CASCADE;
DROP TABLE IF EXISTS job_executions_2023 CASCADE;
DROP TABLE IF EXISTS job_executions_2024 CASCADE;
DROP TABLE IF EXISTS job_executions_2025 CASCADE;
DROP TABLE IF EXISTS job_executions_2026 CASCADE;

DROP TABLE IF EXISTS facebook_ads_data_2016 CASCADE;
DROP TABLE IF EXISTS facebook_ads_data_2017 CASCADE;
DROP TABLE IF EXISTS facebook_ads_data_2018 CASCADE;
DROP TABLE IF EXISTS facebook_ads_data_2019 CASCADE;
DROP TABLE IF EXISTS facebook_ads_data_2020 CASCADE;
DROP TABLE IF EXISTS facebook_ads_data_2021 CASCADE;
DROP TABLE IF EXISTS facebook_ads_data_2022 CASCADE;
DROP TABLE IF EXISTS facebook_ads_data_2023 CASCADE;
DROP TABLE IF EXISTS facebook_ads_data_2024 CASCADE;
DROP TABLE IF EXISTS facebook_ads_data_2025 CASCADE;
DROP TABLE IF EXISTS facebook_ads_data_2026 CASCADE;

DROP TABLE IF EXISTS hotmart_data_2016 CASCADE;
DROP TABLE IF EXISTS hotmart_data_2017 CASCADE;
DROP TABLE IF EXISTS hotmart_data_2018 CASCADE;
DROP TABLE IF EXISTS hotmart_data_2019 CASCADE;
DROP TABLE IF EXISTS hotmart_data_2020 CASCADE;
DROP TABLE IF EXISTS hotmart_data_2021 CASCADE;
DROP TABLE IF EXISTS hotmart_data_2022 CASCADE;
DROP TABLE IF EXISTS hotmart_data_2023 CASCADE;
DROP TABLE IF EXISTS hotmart_data_2024 CASCADE;
DROP TABLE IF EXISTS hotmart_data_2025 CASCADE;
DROP TABLE IF EXISTS hotmart_data_2026 CASCADE;

-- Step 4: Drop main tables
DROP TABLE IF EXISTS job_executions CASCADE;
DROP TABLE IF EXISTS facebook_ads_data CASCADE;
DROP TABLE IF EXISTS hotmart_data CASCADE;
DROP TABLE IF EXISTS api_health_checks CASCADE;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- After running this rollback, run:
-- SELECT * FROM information_schema.tables WHERE table_schema = 'public';
-- Should return ZERO rows for our tables

-- ============================================================================
-- NOTES
-- ============================================================================

-- This rollback is COMPLETE and IRREVERSIBLE
-- Make sure to:
-- 1. Create a backup/snapshot before running this
-- 2. Only run in testing environment unless absolutely necessary
-- 3. Remember that 002_seed_data.sql will need to be re-run if you want data back

-- To restore: Re-run migrations 001 and 002 in order

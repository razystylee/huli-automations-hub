-- Migration: 001_init_schema.sql
-- Description: Initialize database schema for Huli-VELLHUB Phase 2
-- Date: 2026-02-21
-- Idempotent: YES (uses IF NOT EXISTS)

-- ============================================================================
-- TABLE 1: job_executions (Scheduler History)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.job_executions (
  id BIGSERIAL NOT NULL,
  job_id VARCHAR(64) NOT NULL,
  job_name VARCHAR(255) NOT NULL,
  status VARCHAR(20) NOT NULL,
  duration_seconds FLOAT,
  output TEXT,
  errors TEXT,
  executed_at TIMESTAMP WITH TIME ZONE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  retry_count INT DEFAULT 0,
  timeout_seconds INT,
  exit_code INT,
  PRIMARY KEY (id, executed_at)
) PARTITION BY RANGE (executed_at);

-- Create partitions for job_executions (2016-2026) - based on timestamp ranges
CREATE TABLE IF NOT EXISTS job_executions_2016 PARTITION OF job_executions
  FOR VALUES FROM ('2016-01-01'::TIMESTAMP WITH TIME ZONE) TO ('2017-01-01'::TIMESTAMP WITH TIME ZONE);
CREATE TABLE IF NOT EXISTS job_executions_2017 PARTITION OF job_executions
  FOR VALUES FROM ('2017-01-01'::TIMESTAMP WITH TIME ZONE) TO ('2018-01-01'::TIMESTAMP WITH TIME ZONE);
CREATE TABLE IF NOT EXISTS job_executions_2018 PARTITION OF job_executions
  FOR VALUES FROM ('2018-01-01'::TIMESTAMP WITH TIME ZONE) TO ('2019-01-01'::TIMESTAMP WITH TIME ZONE);
CREATE TABLE IF NOT EXISTS job_executions_2019 PARTITION OF job_executions
  FOR VALUES FROM ('2019-01-01'::TIMESTAMP WITH TIME ZONE) TO ('2020-01-01'::TIMESTAMP WITH TIME ZONE);
CREATE TABLE IF NOT EXISTS job_executions_2020 PARTITION OF job_executions
  FOR VALUES FROM ('2020-01-01'::TIMESTAMP WITH TIME ZONE) TO ('2021-01-01'::TIMESTAMP WITH TIME ZONE);
CREATE TABLE IF NOT EXISTS job_executions_2021 PARTITION OF job_executions
  FOR VALUES FROM ('2021-01-01'::TIMESTAMP WITH TIME ZONE) TO ('2022-01-01'::TIMESTAMP WITH TIME ZONE);
CREATE TABLE IF NOT EXISTS job_executions_2022 PARTITION OF job_executions
  FOR VALUES FROM ('2022-01-01'::TIMESTAMP WITH TIME ZONE) TO ('2023-01-01'::TIMESTAMP WITH TIME ZONE);
CREATE TABLE IF NOT EXISTS job_executions_2023 PARTITION OF job_executions
  FOR VALUES FROM ('2023-01-01'::TIMESTAMP WITH TIME ZONE) TO ('2024-01-01'::TIMESTAMP WITH TIME ZONE);
CREATE TABLE IF NOT EXISTS job_executions_2024 PARTITION OF job_executions
  FOR VALUES FROM ('2024-01-01'::TIMESTAMP WITH TIME ZONE) TO ('2025-01-01'::TIMESTAMP WITH TIME ZONE);
CREATE TABLE IF NOT EXISTS job_executions_2025 PARTITION OF job_executions
  FOR VALUES FROM ('2025-01-01'::TIMESTAMP WITH TIME ZONE) TO ('2026-01-01'::TIMESTAMP WITH TIME ZONE);
CREATE TABLE IF NOT EXISTS job_executions_2026 PARTITION OF job_executions
  FOR VALUES FROM ('2026-01-01'::TIMESTAMP WITH TIME ZONE) TO ('2027-01-01'::TIMESTAMP WITH TIME ZONE);

-- Indices for job_executions
CREATE INDEX IF NOT EXISTS idx_job_executions_job_id ON job_executions(job_id);
CREATE INDEX IF NOT EXISTS idx_job_executions_executed_at ON job_executions(executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_executions_status ON job_executions(status);
CREATE INDEX IF NOT EXISTS idx_job_executions_job_status_date
  ON job_executions(job_id, status, executed_at DESC);

-- Enable RLS (prepared for future use, not enabled yet)
ALTER TABLE job_executions ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE job_executions IS 'Scheduler job execution history (10 years partitioned by year)';
COMMENT ON COLUMN job_executions.job_id IS 'Unique job identifier (from jobs_config.json)';
COMMENT ON COLUMN job_executions.status IS 'Execution status: SUCCESS, ERROR, RUNNING, TIMEOUT';
COMMENT ON COLUMN job_executions.executed_at IS 'Execution timestamp (UTC/Sao Paulo)';

-- ============================================================================
-- TABLE 2: facebook_ads_data (FB Ads Historical Data)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.facebook_ads_data (
  id BIGSERIAL NOT NULL,
  account_id VARCHAR(64) NOT NULL,
  campaign_name VARCHAR(255),
  ad_id VARCHAR(64),
  ad_name VARCHAR(255),

  -- Spend & Cost Metrics
  spend DECIMAL(10, 2),
  cpc DECIMAL(8, 2),
  cpm DECIMAL(8, 2),
  cost_per_message DECIMAL(8, 2),
  cost_per_lpv DECIMAL(8, 2),

  -- Volume Metrics
  impressions BIGINT,
  reach BIGINT,
  clicks BIGINT,
  messages BIGINT,
  lpv BIGINT,
  conversions BIGINT,

  -- Engagement Metrics
  frequency DECIMAL(5, 2),
  connect_rate DECIMAL(5, 2),

  -- Timestamps
  date DATE NOT NULL,
  synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Provenance
  source_job_id VARCHAR(64),

  PRIMARY KEY (id, date)
) PARTITION BY RANGE (date);

-- Create partitions for facebook_ads_data (2016-2026) - based on date ranges
CREATE TABLE IF NOT EXISTS facebook_ads_data_2016 PARTITION OF facebook_ads_data
  FOR VALUES FROM ('2016-01-01'::DATE) TO ('2017-01-01'::DATE);
CREATE TABLE IF NOT EXISTS facebook_ads_data_2017 PARTITION OF facebook_ads_data
  FOR VALUES FROM ('2017-01-01'::DATE) TO ('2018-01-01'::DATE);
CREATE TABLE IF NOT EXISTS facebook_ads_data_2018 PARTITION OF facebook_ads_data
  FOR VALUES FROM ('2018-01-01'::DATE) TO ('2019-01-01'::DATE);
CREATE TABLE IF NOT EXISTS facebook_ads_data_2019 PARTITION OF facebook_ads_data
  FOR VALUES FROM ('2019-01-01'::DATE) TO ('2020-01-01'::DATE);
CREATE TABLE IF NOT EXISTS facebook_ads_data_2020 PARTITION OF facebook_ads_data
  FOR VALUES FROM ('2020-01-01'::DATE) TO ('2021-01-01'::DATE);
CREATE TABLE IF NOT EXISTS facebook_ads_data_2021 PARTITION OF facebook_ads_data
  FOR VALUES FROM ('2021-01-01'::DATE) TO ('2022-01-01'::DATE);
CREATE TABLE IF NOT EXISTS facebook_ads_data_2022 PARTITION OF facebook_ads_data
  FOR VALUES FROM ('2022-01-01'::DATE) TO ('2023-01-01'::DATE);
CREATE TABLE IF NOT EXISTS facebook_ads_data_2023 PARTITION OF facebook_ads_data
  FOR VALUES FROM ('2023-01-01'::DATE) TO ('2024-01-01'::DATE);
CREATE TABLE IF NOT EXISTS facebook_ads_data_2024 PARTITION OF facebook_ads_data
  FOR VALUES FROM ('2024-01-01'::DATE) TO ('2025-01-01'::DATE);
CREATE TABLE IF NOT EXISTS facebook_ads_data_2025 PARTITION OF facebook_ads_data
  FOR VALUES FROM ('2025-01-01'::DATE) TO ('2026-01-01'::DATE);
CREATE TABLE IF NOT EXISTS facebook_ads_data_2026 PARTITION OF facebook_ads_data
  FOR VALUES FROM ('2026-01-01'::DATE) TO ('2027-01-01'::DATE);

-- Indices for facebook_ads_data
CREATE INDEX IF NOT EXISTS idx_facebook_ads_account_date
  ON facebook_ads_data(account_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_facebook_ads_campaign_date
  ON facebook_ads_data(campaign_name, date DESC);
CREATE INDEX IF NOT EXISTS idx_facebook_ads_date ON facebook_ads_data(date DESC);

-- Enable RLS (prepared for future use)
ALTER TABLE facebook_ads_data ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE facebook_ads_data IS 'Facebook Ads metrics (10 years, ~200 rows/day)';
COMMENT ON COLUMN facebook_ads_data.date IS 'Date of the metrics snapshot';
COMMENT ON COLUMN facebook_ads_data.account_id IS 'Facebook Ad Account ID';

-- ============================================================================
-- TABLE 3: hotmart_data (Sales History)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.hotmart_data (
  id BIGSERIAL NOT NULL,
  transaction_id VARCHAR(64) NOT NULL,
  transaction_status VARCHAR(20),

  -- Product Info
  product_id VARCHAR(64),
  product_name VARCHAR(255),
  pricing_code VARCHAR(64),

  -- Seller Info
  producer_name VARCHAR(255),
  producer_id VARCHAR(64),

  -- Buyer Info
  buyer_name VARCHAR(255),
  buyer_email VARCHAR(255),

  -- Financial Data
  price DECIMAL(12, 2),
  commissions DECIMAL(10, 2),
  payment_method VARCHAR(50),

  -- Subscription & Installments
  is_subscription BOOLEAN,
  installments INT DEFAULT 1,

  -- Sales Context
  source VARCHAR(100),

  -- Timestamps
  sale_date DATE NOT NULL,
  payment_date DATE,
  synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Provenance
  source_job_id VARCHAR(64),

  PRIMARY KEY (id, sale_date)
) PARTITION BY RANGE (sale_date);

-- Create partitions for hotmart_data (2016-2026) - based on date ranges
CREATE TABLE IF NOT EXISTS hotmart_data_2016 PARTITION OF hotmart_data
  FOR VALUES FROM ('2016-01-01'::DATE) TO ('2017-01-01'::DATE);
CREATE TABLE IF NOT EXISTS hotmart_data_2017 PARTITION OF hotmart_data
  FOR VALUES FROM ('2017-01-01'::DATE) TO ('2018-01-01'::DATE);
CREATE TABLE IF NOT EXISTS hotmart_data_2018 PARTITION OF hotmart_data
  FOR VALUES FROM ('2018-01-01'::DATE) TO ('2019-01-01'::DATE);
CREATE TABLE IF NOT EXISTS hotmart_data_2019 PARTITION OF hotmart_data
  FOR VALUES FROM ('2019-01-01'::DATE) TO ('2020-01-01'::DATE);
CREATE TABLE IF NOT EXISTS hotmart_data_2020 PARTITION OF hotmart_data
  FOR VALUES FROM ('2020-01-01'::DATE) TO ('2021-01-01'::DATE);
CREATE TABLE IF NOT EXISTS hotmart_data_2021 PARTITION OF hotmart_data
  FOR VALUES FROM ('2021-01-01'::DATE) TO ('2022-01-01'::DATE);
CREATE TABLE IF NOT EXISTS hotmart_data_2022 PARTITION OF hotmart_data
  FOR VALUES FROM ('2022-01-01'::DATE) TO ('2023-01-01'::DATE);
CREATE TABLE IF NOT EXISTS hotmart_data_2023 PARTITION OF hotmart_data
  FOR VALUES FROM ('2023-01-01'::DATE) TO ('2024-01-01'::DATE);
CREATE TABLE IF NOT EXISTS hotmart_data_2024 PARTITION OF hotmart_data
  FOR VALUES FROM ('2024-01-01'::DATE) TO ('2025-01-01'::DATE);
CREATE TABLE IF NOT EXISTS hotmart_data_2025 PARTITION OF hotmart_data
  FOR VALUES FROM ('2025-01-01'::DATE) TO ('2026-01-01'::DATE);
CREATE TABLE IF NOT EXISTS hotmart_data_2026 PARTITION OF hotmart_data
  FOR VALUES FROM ('2026-01-01'::DATE) TO ('2027-01-01'::DATE);

-- Indices for hotmart_data
CREATE INDEX IF NOT EXISTS idx_hotmart_sale_date ON hotmart_data(sale_date DESC);
CREATE INDEX IF NOT EXISTS idx_hotmart_producer_date
  ON hotmart_data(producer_id, sale_date DESC);
CREATE INDEX IF NOT EXISTS idx_hotmart_product_date
  ON hotmart_data(product_id, sale_date DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_hotmart_transaction_id ON hotmart_data(transaction_id, sale_date);

-- Enable RLS (prepared for future use)
ALTER TABLE hotmart_data ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE hotmart_data IS 'Hotmart sales transactions (10 years, ~60 rows/day)';
COMMENT ON COLUMN hotmart_data.transaction_id IS 'Unique transaction ID from Hotmart';
COMMENT ON COLUMN hotmart_data.sale_date IS 'Date of sale';

-- ============================================================================
-- TABLE 4: api_health_checks (Health Check Logs)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.api_health_checks (
  id BIGSERIAL NOT NULL,
  api_name VARCHAR(64) NOT NULL,
  endpoint VARCHAR(255),
  status VARCHAR(20) NOT NULL,
  response_time_ms INT,
  error_message TEXT,
  http_status_code INT,
  checked_at TIMESTAMP WITH TIME ZONE NOT NULL,
  job_id VARCHAR(64),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  PRIMARY KEY (id)
);

-- Indices for api_health_checks
CREATE INDEX IF NOT EXISTS idx_api_health_api_name_date
  ON api_health_checks(api_name, checked_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_health_status ON api_health_checks(status);

COMMENT ON TABLE api_health_checks IS 'API health check history (for monitoring before job execution)';
COMMENT ON COLUMN api_health_checks.api_name IS 'API name: google_sheets, facebook_ads, hotmart, google_drive';

-- ============================================================================
-- Grant Permissions (Supabase Public)
-- ============================================================================

GRANT SELECT, INSERT, UPDATE ON job_executions TO authenticated;
GRANT SELECT, INSERT, UPDATE ON facebook_ads_data TO authenticated;
GRANT SELECT, INSERT, UPDATE ON hotmart_data TO authenticated;
GRANT SELECT, INSERT ON api_health_checks TO authenticated;
GRANT USAGE ON SCHEMA public TO anon, authenticated;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================

-- Status: All tables created with partitions and indices
-- Next: Load seed data via 002_seed_data.sql

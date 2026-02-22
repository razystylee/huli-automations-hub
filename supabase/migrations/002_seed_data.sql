-- Migration: 002_seed_data.sql
-- Description: Load initial data from CSV files
-- Date: 2026-02-21
-- Status: READY FOR EXECUTION (see instructions below)

-- ============================================================================
-- INSTRUCTIONS FOR SEED DATA LOADING
-- ============================================================================
--
-- This migration prepares the INSERT statements for seed data.
-- You have TWO options to load the CSV data:
--
-- OPTION A: Using Supabase CSV Import (Recommended - GUI)
-- 1. Go to Supabase Dashboard → SQL Editor
-- 2. For each table:
--    a. Click "Import data"
--    b. Select the CSV file
--    c. Map columns to table schema
--    d. Click "Import"
--
-- OPTION B: Using psql (Command Line)
-- 1. Format: psql -U postgres -h localhost -d postgres -c "\\COPY table_name FROM 'file.csv' WITH (FORMAT csv, HEADER true)"
-- 2. Example:
--    psql -U postgres -h [supabase-host] -d [database] \
--      -c "\\COPY facebook_ads_data(date, account_id, campaign_name, ad_id, ad_name, spend, messages, cost_per_message, clicks, cpc, lpv, cost_per_lpv, connect_rate, impressions, cpm, reach, frequency, conversions, synced_at) \
--      FROM '/path/to/Dados de Tráfego - Facebook Ads - Dados.csv' \
--      WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '\"', ESCAPE '\\')"
--
-- OPTION C: Using Python Script (For integration testing)
-- We provide: supabase/scripts/load_csv_data.py
--
-- ============================================================================

-- IMPORTANT: This file documents the mapping but does NOT execute imports
-- The actual CSV loading should be done via Supabase UI or Python script

-- ============================================================================
-- MAPPING: CSV Columns → Database Columns
-- ============================================================================

-- *** FACEBOOK ADS DATA ***
-- CSV Column → Database Column
-- Data → date
-- Conta → account_id
-- Campanha → campaign_name
-- Conjunto de Anúncios → ad_id
-- Anúncio → ad_name
-- Gasto → spend
-- Mensagens → messages
-- Custo por Mensagem → cost_per_message
-- Cliques → clicks
-- CPC → cpc
-- Landing Page Views → lpv
-- Custo por LPV → cost_per_lpv
-- Connect Rate → connect_rate
-- Impressões → impressions
-- CPM → cpm
-- Alcance → reach
-- Frequência → frequency
-- Compras → conversions
-- Data de Extração → synced_at

-- *** HOTMART DATA ***
-- CSV Column → Database Column
-- ID_Transacao → transaction_id
-- Status → transaction_status
-- Data_Compra → sale_date
-- Data_Aprovacao → payment_date
-- Produto → product_name
-- Produto_ID → product_id
-- Codigo_Preco → pricing_code
-- Valor_Total → price
-- Metodo_Pagamento → payment_method
-- E_Assinatura → is_subscription
-- Recurrency_Number → installments
-- Comissao → commissions
-- Comprador_Nome → buyer_name
-- Comprador_Email → buyer_email
-- Produtor → producer_name
-- Sales_Source → source
-- Data_Extracao → synced_at

-- ============================================================================
-- DATA QUALITY NOTES
-- ============================================================================

-- Facebook Ads CSV:
-- - 2.853 linhas total (1 header + 2.852 dados)
-- - Data range: Verificar primeira coluna
-- - Missing values: Check for NULLs in numeric columns
-- - Encoding: UTF-8 expected

-- Hotmart CSV:
-- - 464 linhas total (1 header + 463 dados)
-- - Data range: Verificar coluna Data_Compra
-- - Missing values: Check E_Assinatura and payment_date
-- - Encoding: UTF-8 expected

-- ============================================================================
-- DATA VALIDATION QUERIES (Run AFTER seed data is loaded)
-- ============================================================================

-- Verify facebook_ads_data loaded successfully
-- SELECT COUNT(*) as total_rows,
--        MIN(date) as earliest_date,
--        MAX(date) as latest_date,
--        COUNT(DISTINCT account_id) as unique_accounts
-- FROM facebook_ads_data;
-- Expected: 2.852 rows, ~X unique accounts

-- Verify hotmart_data loaded successfully
-- SELECT COUNT(*) as total_rows,
--        MIN(sale_date) as earliest_sale,
--        MAX(sale_date) as latest_sale,
--        COUNT(DISTINCT product_id) as unique_products
-- FROM hotmart_data;
-- Expected: 463 rows, X unique products

-- Check data distribution
-- SELECT DATE_TRUNC('month', date) as month, COUNT(*) as count
-- FROM facebook_ads_data
-- GROUP BY DATE_TRUNC('month', date)
-- ORDER BY month DESC;

-- ============================================================================
-- ROLLBACK INSTRUCTIONS
-- ============================================================================

-- If data needs to be cleared (e.g., for re-import):
-- TRUNCATE facebook_ads_data CASCADE;
-- TRUNCATE hotmart_data CASCADE;

-- Then re-run seed data import via Supabase UI or Python script

-- ============================================================================
-- NEXT STEPS
-- ============================================================================

-- 1. Use Supabase CSV Import GUI (RECOMMENDED):
--    - Dashboard → SQL Editor
--    - Table: facebook_ads_data
--    - File: ~/Downloads/Dados de Tráfego - Facebook Ads - Dados.csv
--    - Then repeat for hotmart_data

-- 2. OR use the Python script:
--    - python supabase/scripts/load_csv_data.py \
--        --facebook ~/Downloads/Dados\ de\ Tráfego\ -\ Facebook\ Ads\ -\ Dados.csv \
--        --hotmart ~/Downloads/Todas\ as\ vendas\ Tio\ Huli\ -\ Vendas.csv

-- 3. Validate data loaded (run validation queries above)

-- 4. Then run 003_create_views.sql for analytics views

-- ============================================================================
-- This file is for documentation. Actual CSV import happens separately.
-- ============================================================================

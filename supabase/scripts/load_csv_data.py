#!/usr/bin/env python3
"""
load_csv_data.py - Load CSV data into Supabase PostgreSQL

Usage:
    python load_csv_data.py \
        --facebook "~/Downloads/Dados de Tráfego - Facebook Ads - Dados.csv" \
        --hotmart "~/Downloads/Todas as vendas Tio Huli - Vendas.csv" \
        --project-id cgikjrpmchycolppzcvy

Requirements:
    - python3 with pandas, supabase-py
    - pip install pandas python-dotenv supabase
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Try to import Supabase client
try:
    from supabase import create_client, Client
except ImportError:
    print("ERROR: supabase-py not installed. Install with: pip install supabase")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Load environment variables from .env
load_dotenv(Path(__file__).parent.parent.parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# If not in .env, try to prompt
if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL or SUPABASE_ANON_KEY not found in .env")
    print("Please add these to your .env file or set as environment variables")
    sys.exit(1)

# ============================================================================
# COLUMN MAPPINGS
# ============================================================================

FACEBOOK_ADS_MAPPING = {
    "Data": "date",
    "Conta": "account_id",
    "Campanha": "campaign_name",
    "Conjunto de Anúncios": "ad_id",
    "Anúncio": "ad_name",
    "Gasto": "spend",
    "Mensagens": "messages",
    "Custo por Mensagem": "cost_per_message",
    "Cliques": "clicks",
    "CPC": "cpc",
    "Landing Page Views": "lpv",
    "Custo por LPV": "cost_per_lpv",
    "Connect Rate": "connect_rate",
    "Impressões": "impressions",
    "CPM": "cpm",
    "Alcance": "reach",
    "Frequência": "frequency",
    "Compras": "conversions",
    "Data de Extração": "synced_at",
}

HOTMART_MAPPING = {
    "ID_Transacao": "transaction_id",
    "Status": "transaction_status",
    "Data_Compra": "sale_date",
    "Data_Aprovacao": "payment_date",
    "Produto": "product_name",
    "Produto_ID": "product_id",
    "Codigo_Preco": "pricing_code",
    "Valor_Total": "price",
    "Metodo_Pagamento": "payment_method",
    "E_Assinatura": "is_subscription",
    "Recurrency_Number": "installments",
    "Comissao": "commissions",
    "Comprador_Nome": "buyer_name",
    "Comprador_Email": "buyer_email",
    "Produtor": "producer_name",
    "Sales_Source": "source",
    "Data_Extracao": "synced_at",
}

# ============================================================================
# DATA CLEANING FUNCTIONS
# ============================================================================

def clean_facebook_data(df):
    """Clean and normalize Facebook Ads data"""
    print("  ├─ Cleaning Facebook Ads data...")

    # Rename columns
    df = df.rename(columns=FACEBOOK_ADS_MAPPING)

    # Truncate VARCHAR(64) columns to max 64 chars
    varchar_cols = ["account_id", "ad_id", "campaign_name", "ad_name"]
    for col in varchar_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str[:64]

    # Convert Data to date string (ISO-8601 format for JSON serialization)
    df["date"] = pd.to_datetime(df["date"]).dt.strftime('%Y-%m-%d')

    # Convert numeric columns
    numeric_cols = ["spend", "cost_per_message", "cpc", "cpm", "cost_per_lpv",
                    "connect_rate", "frequency"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert integer columns
    int_cols = ["messages", "clicks", "impressions", "reach", "lpv", "conversions"]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('int64')

    # Set synced_at to current time if empty
    df["synced_at"] = datetime.utcnow().isoformat()

    # Remove rows with missing critical fields
    df = df.dropna(subset=["date", "account_id"])

    # Convert NaN to None for JSON serialization
    df = df.astype(object).where(pd.notna(df), None)

    print(f"  └─ Cleaned: {len(df)} rows")
    return df

def clean_hotmart_data(df):
    """Clean and normalize Hotmart sales data"""
    print("  ├─ Cleaning Hotmart data...")

    # Rename columns
    df = df.rename(columns=HOTMART_MAPPING)

    # Truncate VARCHAR columns to max allowed size
    # product_name and product_id can be up to 255, others up to 64
    varchar_cols = {
        "transaction_id": 64,
        "product_id": 64,
        "pricing_code": 64,
        "producer_name": 255,
        "product_name": 255,
        "source": 100
    }
    for col, max_len in varchar_cols.items():
        if col in df.columns:
            df[col] = df[col].astype(str).str[:max_len]

    # Convert dates to ISO-8601 strings for JSON serialization
    df["sale_date"] = pd.to_datetime(df["sale_date"]).dt.strftime('%Y-%m-%d')
    if "payment_date" in df.columns:
        df["payment_date"] = pd.to_datetime(df["payment_date"], errors='coerce').dt.strftime('%Y-%m-%d')

    # Convert numeric columns
    numeric_cols = ["price", "commissions"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert integer columns
    df["installments"] = pd.to_numeric(df["installments"], errors='coerce').fillna(1).astype('int64')

    # Convert boolean
    if "is_subscription" in df.columns:
        df["is_subscription"] = df["is_subscription"].map(
            {"Sim": True, "Não": False, "SIM": True, "NÃO": False, True: True, False: False}
        ).fillna(False)

    # Set synced_at to current time
    df["synced_at"] = datetime.utcnow().isoformat()

    # Remove rows with missing critical fields
    df = df.dropna(subset=["transaction_id", "sale_date"])

    # Remove duplicate transactions (keep first occurrence)
    df = df.drop_duplicates(subset=["transaction_id", "sale_date"], keep='first')

    # Convert NaN to None for JSON serialization
    df = df.astype(object).where(pd.notna(df), None)

    print(f"  └─ Cleaned: {len(df)} rows")
    return df

# ============================================================================
# SUPABASE UPLOAD FUNCTIONS
# ============================================================================

def upload_to_supabase(client: Client, table_name: str, df: pd.DataFrame, batch_size: int = 1000):
    """Upload dataframe to Supabase table in batches"""
    print(f"  ├─ Uploading to '{table_name}'...")

    total_rows = len(df)
    uploaded = 0

    # Convert NaN to None for JSON serialization
    df = df.where(pd.notna(df), None)

    # Convert dataframe to list of dicts
    records = df.to_dict('records')

    # Upload in batches
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        try:
            response = client.table(table_name).insert(batch).execute()
            uploaded += len(batch)
            print(f"    └─ Progress: {uploaded}/{total_rows} rows uploaded", end='\r')
        except Exception as e:
            print(f"\n  ❌ ERROR uploading batch {i//batch_size + 1}: {str(e)}")
            return False

    print(f"    └─ Successfully uploaded: {uploaded}/{total_rows} rows ✅")
    return True

# ============================================================================
# VERIFICATION FUNCTIONS
# ============================================================================

def verify_data(client: Client, table_name: str, expected_count: int):
    """Verify data was uploaded correctly"""
    print(f"  ├─ Verifying '{table_name}'...")

    try:
        result = client.table(table_name).select("COUNT(*)", count='exact').execute()
        count = result.count

        if count == expected_count:
            print(f"  └─ ✅ Verification passed: {count} rows in database")
            return True
        else:
            print(f"  ⚠️  WARNING: Expected {expected_count} rows, found {count}")
            return True  # Non-critical warning
    except Exception as e:
        print(f"  ❌ ERROR verifying: {str(e)}")
        return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Load CSV data into Supabase PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load both CSVs
  python load_csv_data.py \\
    --facebook ~/Downloads/"Dados de Tráfego - Facebook Ads - Dados.csv" \\
    --hotmart ~/Downloads/"Todas as vendas Tio Huli - Vendas.csv"

  # Load only Facebook
  python load_csv_data.py --facebook ~/Downloads/"Dados de Tráfego - Facebook Ads - Dados.csv"

  # Load only Hotmart
  python load_csv_data.py --hotmart ~/Downloads/"Todas as vendas Tio Huli - Vendas.csv"
        """
    )

    parser.add_argument("--facebook", type=str, help="Path to Facebook Ads CSV file")
    parser.add_argument("--hotmart", type=str, help="Path to Hotmart CSV file")
    parser.add_argument("--batch-size", type=int, default=1000, help="Upload batch size (default: 1000)")
    parser.add_argument("--dry-run", action="store_true", help="Test data cleaning without uploading")

    args = parser.parse_args()

    if not args.facebook and not args.hotmart:
        parser.print_help()
        sys.exit(1)

    # ========================================================================
    # INITIALIZE SUPABASE CLIENT
    # ========================================================================

    print("\n📊 Huli-VELLHUB - CSV Data Loader")
    print("=" * 60)
    print(f"Supabase Project: {SUPABASE_URL}")
    print()

    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {str(e)}")
        sys.exit(1)

    # ========================================================================
    # LOAD FACEBOOK ADS DATA
    # ========================================================================

    if args.facebook:
        print("\n📱 Loading Facebook Ads Data")
        print("-" * 60)

        facebook_path = Path(args.facebook).expanduser()

        if not facebook_path.exists():
            print(f"❌ File not found: {facebook_path}")
            sys.exit(1)

        try:
            print(f"  ├─ Reading: {facebook_path}")
            df_facebook = pd.read_csv(facebook_path)
            print(f"  ├─ Loaded: {len(df_facebook)} rows, {len(df_facebook.columns)} columns")

            df_facebook = clean_facebook_data(df_facebook)

            if not args.dry_run:
                if upload_to_supabase(client, "facebook_ads_data", df_facebook, args.batch_size):
                    verify_data(client, "facebook_ads_data", len(df_facebook))
        except Exception as e:
            print(f"❌ ERROR processing Facebook data: {str(e)}")
            sys.exit(1)

    # ========================================================================
    # LOAD HOTMART DATA
    # ========================================================================

    if args.hotmart:
        print("\n💰 Loading Hotmart Sales Data")
        print("-" * 60)

        hotmart_path = Path(args.hotmart).expanduser()

        if not hotmart_path.exists():
            print(f"❌ File not found: {hotmart_path}")
            sys.exit(1)

        try:
            print(f"  ├─ Reading: {hotmart_path}")
            df_hotmart = pd.read_csv(hotmart_path)
            print(f"  ├─ Loaded: {len(df_hotmart)} rows, {len(df_hotmart.columns)} columns")

            df_hotmart = clean_hotmart_data(df_hotmart)

            if not args.dry_run:
                if upload_to_supabase(client, "hotmart_data", df_hotmart, args.batch_size):
                    verify_data(client, "hotmart_data", len(df_hotmart))
        except Exception as e:
            print(f"❌ ERROR processing Hotmart data: {str(e)}")
            sys.exit(1)

    # ========================================================================
    # COMPLETION
    # ========================================================================

    print("\n" + "=" * 60)
    if args.dry_run:
        print("✅ DRY RUN COMPLETE - No data was uploaded")
    else:
        print("✅ DATA LOADING COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run migration 003_create_views.sql")
    print("  2. Test API endpoints for analytics data")
    print("  3. Verify dashboard loads in < 7 seconds")

if __name__ == "__main__":
    main()

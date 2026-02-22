#!/usr/bin/env python3
"""
Hotmart Sales Daily Extractor → Google Sheets

Extracts daily sales from Hotmart API and appends them to the centralized
"Todas as vendas Tio Huli" Google Sheet.

Usage:
    python3 hotmart_to_sheets.py                    # Extract from yesterday
    python3 hotmart_to_sheets.py --date 2026-02-20  # Extract specific date
    python3 hotmart_to_sheets.py --csv-only         # CSV backup only, no Sheets
"""

import os
import sys
import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Debug: Print startup info
print(f"[DEBUG] Script started at {datetime.now()}")
print(f"[DEBUG] Python version: {sys.version}")
print(f"[DEBUG] Python executable: {sys.executable}")
print(f"[DEBUG] Working directory: {os.getcwd()}")
print(f"[DEBUG] HOME: {os.environ.get('HOME', 'NOT SET')}")
print()

# Load environment variables
env_path = os.path.expanduser('~/.openclaw/secrets/chaves_de_acesso.env')
print(f"[DEBUG] Looking for env file at: {env_path}")
if os.path.exists(env_path):
    print(f"[DEBUG] ✅ Found env file, loading...")
    load_dotenv(env_path)
else:
    print(f"[DEBUG] ⚠️ No env file found, loading from system environment...")
    load_dotenv()

# Try to import Hotmart client
print("[DEBUG] Attempting to import hotmart_python...")
try:
    from hotmart_python import Hotmart
    print("[DEBUG] ✅ Successfully imported hotmart_python")
except ImportError as e:
    print(f"❌ ERROR: Cannot import hotmart_python: {e}")
    print("ℹ️ Run: pip install hotmart-python")
    sys.exit(1)


class HotmartExtractor:
    """Extract sales from Hotmart API"""

    def __init__(self):
        """Initialize with credentials from environment"""
        self.client_id = os.getenv('HOTMART_CLIENT_ID')
        self.client_secret = os.getenv('HOTMART_CLIENT_SECRET')
        self.basic_token = os.getenv('HOTMART_BASIC_TOKEN')

        self.sheet_id = os.getenv('HOTMART_SHEET_ID', '1WIddZ96vTvaZ9engZuP4L3DOlPhiUoWpz_RWu0oG_0U')
        self.validate_hotmart_credentials()

        # Initialize Hotmart client
        self.client = Hotmart(
            client_id=self.client_id,
            client_secret=self.client_secret,
            basic=self.basic_token
        )

    def validate_hotmart_credentials(self):
        """Validate that all required Hotmart credentials are present"""
        missing = []
        if not self.client_id:
            missing.append('HOTMART_CLIENT_ID')
        if not self.client_secret:
            missing.append('HOTMART_CLIENT_SECRET')
        if not self.basic_token:
            missing.append('HOTMART_BASIC_TOKEN')

        if missing:
            print(f"❌ ERROR: Missing Hotmart credentials: {', '.join(missing)}")
            print("ℹ️ Configure in Railway or ~/.openclaw/secrets/chaves_de_acesso.env")
            sys.exit(1)

    def extract_sales(self, date_str: str) -> List[Dict]:
        """
        Extract sales from Hotmart for a specific date

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            List of sale dictionaries from Hotmart API
        """
        try:
            # Parse date and create time range (full day)
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            start_ts = int(date_obj.replace(hour=0, minute=0, second=0).timestamp() * 1000)
            end_ts = int(date_obj.replace(hour=23, minute=59, second=59).timestamp() * 1000)

            print(f"📡 Extracting Hotmart sales for {date_str}...")

            # Call Hotmart API
            sales = self.client.get_sales_history(
                start_date=start_ts,
                end_date=end_ts
            )

            print(f"✅ Found {len(sales)} sales")
            return sales

        except Exception as e:
            print(f"❌ ERROR extracting from Hotmart: {e}")
            return []


class DataFormatter:
    """Format Hotmart raw data into Google Sheets format"""

    @staticmethod
    def format_timestamp(timestamp_ms: Optional[int]) -> str:
        """Convert milliseconds timestamp to readable format"""
        if not timestamp_ms:
            return ''
        try:
            timestamp_s = int(timestamp_ms) / 1000
            dt = datetime.fromtimestamp(timestamp_s)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return str(timestamp_ms)

    @staticmethod
    def format_sales(sales: List[Dict]) -> List[List]:
        """
        Format raw sales data into 17 columns for Google Sheets

        Returns:
            List of rows, each row is a list of 17 values
        """
        rows = []

        for sale in sales:
            purchase = sale.get('purchase', {})
            product = sale.get('product', {})
            buyer = sale.get('buyer', {})
            producer = sale.get('producer', {})

            # Extract offer code
            offer_code = ''
            if purchase.get('offer'):
                offer_code = purchase['offer'].get('code', '')

            # Extract sales source (from tracking)
            sales_source = ''
            if purchase.get('tracking'):
                sales_source = purchase['tracking'].get('source', '')

            # Is subscription?
            is_subscription = 'Sim' if purchase.get('recurrency_number') else 'Não'

            row = [
                purchase.get('transaction', ''),           # 1. ID_Transacao
                purchase.get('status', ''),                # 2. Status
                DataFormatter.format_timestamp(
                    purchase.get('order_date')
                ),                                          # 3. Data_Compra
                DataFormatter.format_timestamp(
                    purchase.get('approved_date')
                ),                                          # 4. Data_Aprovacao
                product.get('name', ''),                   # 5. Produto
                product.get('id', ''),                     # 6. Produto_ID
                offer_code,                                # 7. Codigo_Preco
                purchase.get('price', {}).get('value', ''),  # 8. Valor_Total
                purchase.get('payment', {}).get('type', ''),  # 9. Metodo_Pagamento
                is_subscription,                           # 10. E_Assinatura
                purchase.get('recurrency_number', ''),     # 11. Recurrency_Number
                purchase.get('commission', {}).get('value', ''),  # 12. Comissao
                buyer.get('name', ''),                     # 13. Comprador_Nome
                buyer.get('email', ''),                    # 14. Comprador_Email
                producer.get('name', ''),                  # 15. Produtor
                sales_source,                              # 16. Sales_Source
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # 17. Data_Extracao
            ]
            rows.append(row)

        return rows


class SheetsUploader:
    """Upload data to Google Sheets"""

    HEADERS = [
        'ID_Transacao', 'Status', 'Data_Compra', 'Data_Aprovacao',
        'Produto', 'Produto_ID', 'Codigo_Preco', 'Valor_Total', 'Metodo_Pagamento',
        'E_Assinatura', 'Recurrency_Number', 'Comissao',
        'Comprador_Nome', 'Comprador_Email', 'Produtor', 'Sales_Source', 'Data_Extracao'
    ]

    def __init__(self):
        """Initialize Google Sheets credentials"""
        self.validate_google_credentials()

    def validate_google_credentials(self):
        """Validate Google credentials are configured"""
        if not os.getenv('GOOGLE_CREDENTIALS_JSON'):
            print("❌ ERROR: GOOGLE_CREDENTIALS_JSON not configured")
            print("ℹ️ Configure in Railway environment variables")
            sys.exit(1)

        if not os.getenv('GOOGLE_REFRESH_TOKEN'):
            print("❌ ERROR: GOOGLE_REFRESH_TOKEN not configured")
            print("ℹ️ Run: python3 get_refresh_token.py locally and copy token to Railway")
            sys.exit(1)

    def upload(self, rows: List[List], sheet_id: str) -> bool:
        """
        Upload rows to Google Sheets

        Args:
            rows: List of 17-column rows
            sheet_id: Google Sheet ID

        Returns:
            True if successful, False otherwise
        """
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError

            print(f"📤 Uploading {len(rows)} rows to Google Sheets...")

            # Parse credentials JSON
            creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            creds_dict = json.loads(creds_json)

            # Create credentials with refresh token
            refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=creds_dict['installed']['client_id'],
                client_secret=creds_dict['installed']['client_secret']
            )

            # Refresh token if needed
            creds.refresh(Request())

            # Build Sheets service
            service = build('sheets', 'v4', credentials=creds)

            # Append rows to sheet
            body = {'values': rows}
            result = service.spreadsheets().values().append(
                spreadsheetId=sheet_id,
                range='Vendas!A:Q',
                valueInputOption='RAW',
                body=body
            ).execute()

            updated_rows = result.get('updates', {}).get('updatedRows', len(rows))
            print(f"✅ Successfully uploaded {updated_rows} rows")
            return True

        except Exception as e:
            print(f"❌ ERROR uploading to Sheets: {e}")
            import traceback
            traceback.print_exc()
            return False


class CSVBackup:
    """Create local CSV backup of extracted data"""

    @staticmethod
    def save(rows: List[List], date_str: str) -> Optional[str]:
        """
        Save data to CSV file for backup

        Args:
            rows: List of 17-column rows
            date_str: Date in YYYY-MM-DD format

        Returns:
            Path to CSV file, or None if failed
        """
        # Try multiple possible directories
        possible_dirs = [
            os.path.expanduser('~/Desktop/Brain/automations/hotmart/vendas'),
            '/tmp/hotmart_vendas'
        ]

        output_dir = None
        for dir_path in possible_dirs:
            try:
                os.makedirs(dir_path, exist_ok=True)
                output_dir = dir_path
                break
            except Exception as e:
                print(f"⚠️ Cannot create {dir_path}: {e}")
                continue

        if not output_dir:
            print("⚠️ WARNING: No directory available for CSV backup")
            return None

        try:
            filename = f"{output_dir}/vendas_{date_str}.csv"

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                # Write headers
                writer.writerow(SheetsUploader.HEADERS)
                # Write data
                writer.writerows(rows)

            print(f"💾 CSV backup saved: {filename}")
            return filename

        except Exception as e:
            print(f"⚠️ ERROR creating CSV backup: {e}")
            return None


def get_yesterday() -> str:
    """Get yesterday's date in YYYY-MM-DD format"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')


def main():
    """Main execution flow"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract daily sales from Hotmart to Google Sheets'
    )
    parser.add_argument(
        '--date', '-d',
        help='Date to extract (YYYY-MM-DD, default: yesterday)'
    )
    parser.add_argument(
        '--csv-only',
        action='store_true',
        help='Create CSV backup only, do not upload to Sheets'
    )

    args = parser.parse_args()

    # Determine date to process
    date_str = args.date or get_yesterday()
    print(f"\n🚀 Hotmart Sales Extractor")
    print(f"📅 Processing date: {date_str}\n")

    try:
        # 1. Extract from Hotmart
        extractor = HotmartExtractor()
        sales = extractor.extract_sales(date_str)

        if not sales:
            print("⚠️ No sales found for this date")
            return

        # 2. Format data
        formatter = DataFormatter()
        rows = formatter.format_sales(sales)
        print(f"📊 Formatted {len(rows)} rows for Sheets")

        # 3. Create CSV backup
        CSVBackup.save(rows, date_str)

        # 4. Upload to Sheets (unless --csv-only)
        if not args.csv_only:
            uploader = SheetsUploader()
            uploader.upload(rows, extractor.sheet_id)

        print("\n✅ Execution completed successfully\n")

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

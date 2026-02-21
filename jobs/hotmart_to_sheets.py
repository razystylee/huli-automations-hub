#!/usr/bin/env python3
"""
Hotmart to Sheets - Extrai vendas da Hotmart e envia para Google Sheets
Fluxo automático de extração e centralização de vendas
"""

import os
import sys
import csv
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from hotmart_python import Hotmart

# Carregar variáveis de ambiente
env_path = os.path.expanduser('~/.openclaw/secrets/chaves_de_acesso.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ Credenciais carregadas de: {env_path}")
else:
    print(f"⚠️ Arquivo de credenciais não encontrado: {env_path}")
    load_dotenv()

# ID da planilha central "Todas as vendas Tio Huli"
# Local: Pasta "Análises - Funis Tio Huli" no Drive
DEFAULT_SHEET_ID = "1WIddZ96vTvaZ9engZuP4L3DOlPhiUoWpz_RWu0oG_0U"


def get_yesterday():
    """Retorna a data de ontem no formato YYYY-MM-DD"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')


def extract_hotmart_sales(date_str):
    """Extrai vendas da Hotmart para uma data específica"""
    try:
        # Carrega credenciais
        client_id = os.getenv('HOTMART_CLIENT_ID')
        client_secret = os.getenv('HOTMART_CLIENT_SECRET')
        basic_token = os.getenv('HOTMART_BASIC_TOKEN')
        
        if not all([client_id, client_secret, basic_token]):
            print("❌ Credenciais da Hotmart não encontradas no .env")
            return []
        
        # Inicializa cliente Hotmart
        hotmart = Hotmart(
            client_id=client_id,
            client_secret=client_secret,
            basic=basic_token
        )
        
        # Converte data para timestamp
        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        start_ts = int(date_obj.replace(hour=0, minute=0, second=0).timestamp() * 1000)
        end_ts = int(date_obj.replace(hour=23, minute=59, second=59).timestamp() * 1000)
        
        # Busca vendas do dia
        print(f"📊 Extraindo vendas de {date_str}...")
        sales = hotmart.get_sales_history(
            start_date=start_ts,
            end_date=end_ts
        )
        
        print(f"✅ {len(sales)} vendas encontradas")
        return sales
        
    except Exception as e:
        print(f"❌ Erro ao extrair vendas: {e}")
        import traceback
        traceback.print_exc()
        return []


def format_for_sheets(sales):
    """Formata os dados das vendas para o formato do Google Sheets"""
    formatted_rows = []
    
    for sale in sales:
        purchase = sale.get('purchase', {})
        product = sale.get('product', {})
        buyer = sale.get('buyer', {})
        producer = sale.get('producer', {})
        
        # Código do preço (offer code) - essencial para análise
        offer_code = purchase.get('offer', {}).get('code', '') if purchase.get('offer') else ''
        
        # Sales source (origem da venda) - tracking
        tracking = purchase.get('tracking', {}) or {}
        sales_source = tracking.get('source', '') if tracking else ''
        
        row = [
            purchase.get('transaction', ''),  # ID_Transacao
            purchase.get('status', ''),  # Status
            format_date(purchase.get('order_date')),  # Data_Compra
            format_date(purchase.get('approved_date')),  # Data_Aprovacao
            product.get('name', ''),  # Produto
            product.get('id', ''),  # Produto_ID
            offer_code,  # Codigo_Preco
            purchase.get('price', {}).get('value', ''),  # Valor_Total
            purchase.get('payment', {}).get('type', ''),  # Metodo_Pagamento
            'Sim' if purchase.get('recurrency_number') else 'Não',  # E_Assinatura
            purchase.get('recurrency_number', ''),  # Recurrency_Number
            purchase.get('commission', {}).get('value', ''),  # Comissao
            buyer.get('name', ''),  # Comprador_Nome
            buyer.get('email', ''),  # Comprador_Email
            producer.get('name', ''),  # Produtor
            sales_source,  # Sales_Source (NOVO!)
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Data_Extracao
        ]
        formatted_rows.append(row)
    
    return formatted_rows


def format_date(timestamp_ms):
    """Converte timestamp em milissegundos para data legível"""
    if not timestamp_ms:
        return ''
    try:
        timestamp_s = int(timestamp_ms) / 1000
        dt = datetime.fromtimestamp(timestamp_s)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(timestamp_ms)


def save_to_csv(sales, date_str):
    """Salva vendas em CSV localmente (backup)"""
    output_dir = os.path.expanduser('~/Desktop/Brain/automations/hotmart/vendas')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{output_dir}/vendas_{date_str}.csv"
    
    # Headers
    headers = [
        'ID_Transacao', 'Status', 'Data_Compra', 'Data_Aprovacao',
        'Produto', 'Produto_ID', 'Codigo_Preco', 'Valor_Total', 'Metodo_Pagamento',
        'E_Assinatura', 'Recurrency_Number', 'Comissao',
        'Comprador_Nome', 'Comprador_Email', 'Produtor', 'Sales_Source', 'Data_Extracao'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(headers)
        
        for sale in sales:
            purchase = sale.get('purchase', {})
            product = sale.get('product', {})
            buyer = sale.get('buyer', {})
            producer = sale.get('producer', {})
            
            # Código do preço (offer code)
            offer_code = purchase.get('offer', {}).get('code', '') if purchase.get('offer') else ''
            
            # Sales source (origem da venda) - tracking
            tracking = purchase.get('tracking', {}) or {}
            sales_source = tracking.get('source', '') if tracking else ''
            
            row = [
                purchase.get('transaction', ''),
                purchase.get('status', ''),
                format_date(purchase.get('order_date')),
                format_date(purchase.get('approved_date')),
                product.get('name', ''),
                product.get('id', ''),
                offer_code,  # NOVO: Código do Preço
                purchase.get('price', {}).get('value', ''),
                purchase.get('payment', {}).get('type', ''),
                'Sim' if purchase.get('recurrency_number') else 'Não',
                purchase.get('recurrency_number', ''),
                purchase.get('commission', {}).get('value', ''),
                buyer.get('name', ''),
                buyer.get('email', ''),
                producer.get('name', ''),
                sales_source,  # NOVO: Sales_Source
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            ]
            writer.writerow(row)
    
    print(f"💾 CSV salvo: {filename}")
    return filename


def send_to_sheets(rows, sheet_id, range_name="Vendas!A:Q"):
    """Envia dados para Google Sheets usando gog"""
    if not rows:
        print("⚠️ Nenhum dado para enviar")
        return False
    
    if not sheet_id:
        print("❌ ID da planilha não configurado")
        print("💡 Crie a planilha 'Todas as vendas Tio Huli' e configure o ID")
        return False
    
    try:
        print(f"📤 Enviando {len(rows)} vendas para o Sheets...")
        
        # Prepara os valores como JSON
        values_json = json.dumps(rows)
        
        # Usa gog para fazer append
        import subprocess
        cmd = [
            'gog', 'sheets', 'append', sheet_id, range_name,
            '--values-json', values_json,
            '--insert', 'INSERT_ROWS',
            '--account', 'margotvellanibot@gmail.com'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {len(rows)} vendas inseridas na planilha!")
            return True
        else:
            print(f"❌ Erro ao enviar: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Hotmart to Sheets')
    parser.add_argument('--data', '-d', help='Data no formato YYYY-MM-DD (padrão: ontem)')
    parser.add_argument('--sheet-id', '-s', help='ID da planilha do Google Sheets')
    parser.add_argument('--csv-only', action='store_true', help='Apenas gerar CSV, não enviar para Sheets')
    
    args = parser.parse_args()
    
    # Determina a data
    date_str = args.data or get_yesterday()
    print(f"🚀 Iniciando extração para {date_str}")
    
    # Extrai vendas
    sales = extract_hotmart_sales(date_str)
    
    if not sales:
        print("⚠️ Nenhuma venda encontrada para esta data")
        return
    
    # Salva CSV local (backup)
    csv_file = save_to_csv(sales, date_str)
    
    # Se não é apenas CSV, envia para Sheets
    if not args.csv_only:
        # Usa ID fornecido ou o padrão
        sheet_id = args.sheet_id or DEFAULT_SHEET_ID
        
        if sheet_id:
            # Formata para Sheets
            rows = format_for_sheets(sales)
            # Envia para Sheets
            send_to_sheets(rows, sheet_id)
        else:
            print("\n⚠️ ID da planilha não configurado")
            print("Para enviar automaticamente para o Sheets:")
            print("1. Crie uma planilha chamada 'Todas as vendas Tio Huli'")
            print("2. Coloque o ID da planilha na variável DEFAULT_SHEET_ID")
            print(f"3. CSV foi salvo em: {csv_file}")


if __name__ == '__main__':
    main()

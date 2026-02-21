#!/usr/bin/env python3
"""
Facebook Ads to Sheets - Extrai dados de tráfego do Facebook e envia para Google Sheets
Baseado no workflow do N8N - 3 contas: MDGE, M3C, Código MB
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carregar variáveis de ambiente
env_path = os.path.expanduser('~/.openclaw/secrets/facebook_ads.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    print(f"❌ Arquivo de credenciais não encontrado: {env_path}")
    sys.exit(1)

# Configurações
FACEBOOK_API_VERSION = os.getenv('FACEBOOK_API_VERSION', 'v23.0')
ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN')
BASE_URL = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}"

# Contas de anúncios (remove o 'act_' se estiver presente)
AD_ACCOUNTS = {
    'TH03-CA01 (CDO)': os.getenv('META_AD_ACCOUNT_TH03CA01', '').replace('act_', ''),
    '002 - Tio Huli (Lançamento) - M3C': os.getenv('META_AD_ACCOUNT_002_TH_M3C', '').replace('act_', ''),
    '002 - Tio Huli (Lançamento) - CMB': os.getenv('META_AD_ACCOUNT_002_TH_CMB', '').replace('act_', ''),
    'CONTA 4 (847475096345167)': os.getenv('META_AD_ACCOUNT_NOVA4', '').replace('act_', ''),
    'CONTA 5 (1017704976612498)': os.getenv('META_AD_ACCOUNT_NOVA5', '').replace('act_', '')
}

# Filtros de campanha (baseado no workflow N8N)
CAMPAIGN_FILTERS = {
    'TH03-CA01 (CDO)': 'MDGE',
    '002 - Tio Huli (Lançamento) - M3C': 'MTC_TER | CADASTRO | WEBIORICO',
    '002 - Tio Huli (Lançamento) - CMB': 'CODIGOMB',
    'CONTA 4': '',
    'CONTA 5': ''
}


def get_yesterday():
    """Retorna a data de ontem no formato YYYY-MM-DD"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')


def fetch_facebook_insights(account_id, since_date, until_date):
    """Busca insights do Facebook Ads com paginação"""
    url = f"{BASE_URL}/act_{account_id}/insights"
    all_data = []
    after = None
    
    while True:
        params = {
            'access_token': ACCESS_TOKEN,
            'time_increment': 1,  # Dados diários
            'level': 'ad',  # Nível de anúncio
            'fields': 'campaign_name,adset_name,ad_name,spend,impressions,reach,actions',
            'limit': 1000,
            'time_range': json.dumps({'since': since_date, 'until': until_date})
        }
        
        if after:
            params['after'] = after
        
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                print(f"❌ Erro na API: {data['error']['message']}")
                return []
            
            results = data.get('data', [])
            all_data.extend(results)
            
            # Verifica se há mais páginas
            paging = data.get('paging', {})
            cursors = paging.get('cursors', {})
            after = cursors.get('after')
            
            # Se não tem 'next' ou não tem 'after', terminamos
            if not paging.get('next') or not after:
                break
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição: {e}")
            return []
    
    return all_data


def process_actions(actions):
    """Processa as ações e retorna métricas calculadas"""
    metrics = {
        'mensagens': 0,
        'cliques': 0,
        'landing_page_views': 0,
        'compras': 0
    }
    
    if not actions:
        return metrics
    
    for action in actions:
        action_type = action.get('action_type', '')
        value = int(action.get('value', 0))
        
        if action_type == 'onsite_conversion.messaging_conversation_started_7d':
            metrics['mensagens'] = value
        elif action_type == 'link_click':
            metrics['cliques'] = value
        elif action_type == 'purchase':
            metrics['compras'] = value
        elif action_type == 'landing_page_view':
            metrics['landing_page_views'] = value
    
    return metrics


def calculate_kpis(spend, impressions, reach, actions):
    """Calcula KPIs baseados nas métricas"""
    sp = float(spend or 0)
    impr = int(impressions or 0)
    rch = int(reach or 0)
    
    metrics = process_actions(actions)
    
    # Cálculos
    cpm = round(sp / (impr / 1000), 2) if impr > 0 else 0
    cpc = round(sp / metrics['cliques'], 2) if metrics['cliques'] > 0 else 0
    frequencia = round(impr / rch, 2) if rch > 0 else 0
    custo_por_mensagem = round(sp / metrics['mensagens'], 2) if metrics['mensagens'] > 0 else 0
    custo_por_lpv = round(sp / metrics['landing_page_views'], 2) if metrics['landing_page_views'] > 0 else 0
    
    # Connect Rate = taxa de LP views vs cliques (quantos % dos cliques viraram LP views)
    connect_rate = round((metrics['landing_page_views'] / metrics['cliques']) * 100, 2) if metrics['cliques'] > 0 else 0
    
    return {
        **metrics,
        'cpm': cpm,
        'cpc': cpc,
        'frequencia': frequencia,
        'custo_por_mensagem': custo_por_mensagem,
        'custo_por_lpv': custo_por_lpv,
        'connect_rate': connect_rate
    }


def format_data_for_sheets(insights, account_name):
    """Formata os dados para o Google Sheets"""
    formatted_rows = []
    
    for insight in insights:
        spend = float(insight.get('spend', 0))
        impressions = int(insight.get('impressions', 0))
        reach = int(insight.get('reach', 0))
        actions = insight.get('actions', [])
        
        kpis = calculate_kpis(spend, impressions, reach, actions)
        
        # Data formatada
        date_str = insight.get('date_start', '')
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%Y-%m-%dT00:00:00-03:00')
        except:
            formatted_date = date_str
        
        row = [
            formatted_date,  # Data
            account_name,  # Conta
            insight.get('campaign_name', ''),  # Campanha
            insight.get('adset_name', ''),  # Conjunto de Anúncios
            insight.get('ad_name', ''),  # Anúncio
            round(spend, 2),  # Gasto
            kpis['mensagens'],  # Mensagens
            kpis['custo_por_mensagem'],  # Custo por Mensagem
            kpis['cliques'],  # Cliques
            kpis['cpc'],  # CPC
            kpis['landing_page_views'],  # Landing Page Views
            kpis['custo_por_lpv'],  # Custo por LPV
            kpis['connect_rate'],  # Connect Rate (%)
            impressions,  # Impressões
            kpis['cpm'],  # CPM
            reach,  # Alcance
            kpis['frequencia'],  # Frequência
            kpis['compras'],  # Compras
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Data de Extração
        ]
        formatted_rows.append(row)
    
    return formatted_rows


def send_to_sheets(rows, sheet_id, range_name="Dados!A:S"):
    """Envia dados para Google Sheets usando gog"""
    if not rows:
        print("⚠️ Nenhum dado para enviar")
        return False
    
    try:
        print(f"📤 Enviando {len(rows)} registros para o Sheets...")
        
        import subprocess
        values_json = json.dumps(rows)
        
        cmd = [
            'gog', 'sheets', 'append', sheet_id, range_name,
            '--values-json', values_json,
            '--insert', 'INSERT_ROWS',
            '--account', 'margotvellanibot@gmail.com'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {len(rows)} registros inseridos na planilha!")
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
    
    parser = argparse.ArgumentParser(description='Facebook Ads to Sheets')
    parser.add_argument('--data', '-d', help='Data no formato YYYY-MM-DD (padrão: ontem)')
    parser.add_argument('--sheet-id', '-s', help='ID da planilha do Google Sheets')
    parser.add_argument('--conta', '-c', 
                        choices=['TH03-CA01 (CDO)', '002 - Tio Huli (Lançamento) - M3C', 
                                '002 - Tio Huli (Lançamento) - CMB', 'CONTA 4 (847475096345167)', 
                                'CONTA 5 (1017704976612498)', 'todas'], 
                        default='todas', help='Qual conta extrair')
    
    args = parser.parse_args()
    
    # Determina a data
    date_str = args.data or get_yesterday()
    print(f"🚀 Iniciando extração para {date_str}")
    print(f"📊 Contas: {args.conta}")
    print()
    
    all_rows = []
    
    # Extrai dados de cada conta
    accounts_to_process = AD_ACCOUNTS.keys() if args.conta == 'todas' else [args.conta]
    
    for account_name in accounts_to_process:
        account_id = AD_ACCOUNTS[account_name]
        if not account_id:
            print(f"⚠️ Conta {account_name} não configurada, pulando...")
            continue
        
        print(f"📡 Extraindo {account_name}...")
        print(f"   ID da Conta: {account_id}")
        insights = fetch_facebook_insights(account_id, date_str, date_str)
        
        if insights:
            rows = format_data_for_sheets(insights, account_name)
            all_rows.extend(rows)
            print(f"   ✅ {len(rows)} registros extraídos")
        else:
            print(f"   ⚠️ Nenhum dado encontrado")
        print()
    
    # Resumo
    print(f"📊 Total de registros: {len(all_rows)}")
    
    # Usa sheet_id dos argumentos ou do .env
    sheet_id = args.sheet_id or os.getenv('FACEBOOK_SHEET_ID')
    
    if all_rows and sheet_id:
        send_to_sheets(all_rows, sheet_id)
    elif all_rows:
        print("\n⚠️ ID da planilha não fornecido. Dados não enviados.")
        print("Configure FACEBOOK_SHEET_ID no .env ou use --sheet-id")
    else:
        print("\n⚠️ Nenhum dado extraído.")


if __name__ == '__main__':
    main()

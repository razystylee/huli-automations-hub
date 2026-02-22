#!/usr/bin/env python3
"""
Script para gerar um refresh token do Google
Execute localmente no seu computador
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes necessários
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Carregar credenciais do arquivo
with open('google_credentials.json', 'r') as f:
    credentials_dict = json.load(f)

# Criar flow
flow = InstalledAppFlow.from_client_config(credentials_dict, SCOPES)

# Executar autenticação (abre navegador)
creds = flow.run_local_server(port=0)

# Extrair refresh token
refresh_token = creds.refresh_token

print("\n" + "="*60)
print("✅ REFRESH TOKEN OBTIDO COM SUCESSO!")
print("="*60)
print(f"\nRefresh Token:\n{refresh_token}\n")
print("="*60)
print("\nCopie o token acima e adicione no Railway como:")
print("  Nome: GOOGLE_REFRESH_TOKEN")
print("  Valor: (cole o token)")
print("="*60)

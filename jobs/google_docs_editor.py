#!/usr/bin/env python3
"""
Google Docs Editor - Cria e edita documentos no Google Docs
Usa as mesmas credenciais OAuth do gog
"""

import os
import sys
import json
import pickle
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scopes necessários
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

# Caminho das credenciais
CREDENTIALS_PATH = os.path.expanduser('~/.config/google-mcp-server/credentials.json')
TOKEN_PATH = os.path.expanduser('~/.config/google-mcp-server/token.pickle')


def get_credentials():
    """Obtém ou atualiza credenciais OAuth"""
    creds = None
    
    # Carrega token existente
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    
    # Se não tem credenciais válidas, faz login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                print(f"❌ Arquivo de credenciais não encontrado: {CREDENTIALS_PATH}")
                sys.exit(1)
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Salva token
        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds


def create_document(title, content_html=None, folder_id=None):
    """Cria um novo documento Google Docs"""
    try:
        creds = get_credentials()
        
        # Cria documento via Drive API (permite especificar pasta)
        drive_service = build('drive', 'v3', credentials=creds)
        docs_service = build('docs', 'v1', credentials=creds)
        
        # Metadata do arquivo
        file_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.document',
        }
        
        # Se especificou pasta, adiciona parents
        if folder_id:
            file_metadata['parents'] = [folder_id]
            print(f"📁 Salvando na pasta: {folder_id}")
        
        # Cria documento
        doc_result = drive_service.files().create(body=file_metadata).execute()
        doc_id = doc_result.get('id')
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        
        print(f"✅ Documento criado: {title}")
        print(f"🔗 Link: {doc_url}")
        
        # Se tem conteúdo, insere
        if content_html:
            insert_content(docs_service, doc_id, content_html)
        
        return doc_id, doc_url
        
    except HttpError as e:
        print(f"❌ Erro ao criar documento: {e}")
        return None, None


def insert_content(service, doc_id, content_html):
    """Insere conteúdo no documento"""
    try:
        # Converte HTML simples para requests de batchUpdate
        requests = []
        
        # Por enquanto, insere como texto simples
        # (A formatação completa requer parsing mais complexo)
        requests.append({
            'insertText': {
                'location': {
                    'index': 1
                },
                'text': content_html
            }
        })
        
        service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        print("✅ Conteúdo inserido")
        
    except HttpError as e:
        print(f"❌ Erro ao inserir conteúdo: {e}")


def create_from_markdown(title, markdown_path, folder_id=None):
    """Cria documento a partir de arquivo Markdown"""
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return create_document(title, content, folder_id)
        
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {markdown_path}")
        return None, None


def list_documents(max_results=10):
    """Lista documentos no Drive"""
    try:
        creds = get_credentials()
        service = build('drive', 'v3', credentials=creds)
        
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.document'",
            pageSize=max_results,
            fields="nextPageToken, files(id, name, modifiedTime)"
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            print('📭 Nenhum documento encontrado.')
        else:
            print('📄 Documentos encontrados:')
            for item in items:
                print(f"  - {item['name']} ({item['modifiedTime']})")
                print(f"    https://docs.google.com/document/d/{item['id']}/edit")
        
        return items
        
    except HttpError as e:
        print(f"❌ Erro ao listar documentos: {e}")
        return []


if __name__ == '__main__':
    import argparse
    
    # ID da pasta padrão para análises
    DEFAULT_FOLDER_ID = "1Vth0qFLjX-QJbU9I2fKA4PYa3dxLzE50"
    
    parser = argparse.ArgumentParser(description='Google Docs Editor')
    parser.add_argument('--create', '-c', help='Criar novo documento com título')
    parser.add_argument('--markdown', '-m', help='Criar a partir de arquivo Markdown')
    parser.add_argument('--content', '-t', help='Conteúdo do documento')
    parser.add_argument('--folder', '-f', default=DEFAULT_FOLDER_ID, 
                        help=f'ID da pasta do Drive (padrão: {DEFAULT_FOLDER_ID})')
    parser.add_argument('--list', '-l', action='store_true', help='Listar documentos')
    
    args = parser.parse_args()
    
    if args.list:
        list_documents()
    elif args.markdown:
        title = args.create or os.path.basename(args.markdown).replace('.md', '')
        create_from_markdown(title, args.markdown, args.folder)
    elif args.create:
        create_document(args.create, args.content, args.folder)
    else:
        parser.print_help()

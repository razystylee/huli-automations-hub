#!/usr/bin/env python3
"""
HULI Consolidator
Consolida dados de Facebook Ads e Hotmart na Planilha HULI
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configuração de logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"consolidator_{datetime.now().strftime('%Y-%m-%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# IDs das Planilhas (do TOOLS.md e documentos)
PLANILHA_TRAFEGO_ID = "1eHHqpErnVaodZhgyHQSg-PjXv4Z8Et6u9dabpODyLr0"
PLANILHA_VENDAS_ID = "1WIddZ96vTvaZ9engZuP4L3DOlPhiUoWpz_RWu0oG_0U"
PLANILHA_HULI_ID = "1QAvr_4aNmtJMCGlr_UgFufMuJWStRgkYKs52pxz6xAk"
PLANILHA_2UL_ID = "1zp9b345wFXzwfHJJVZqvnl-cRc3yZqfoUgnLhiZzhuw"
PLANILHA_LEADS_ID = "1KUdnJv-fIK3wF3Ii24kCm5uZk24DSMmzlG6FUbqB7T8"  # Nova planilha de leads

class HuliConsolidator:
    def __init__(self, data_referencia=None):
        self.data_referencia = data_referencia or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.data_ontem = (datetime.strptime(self.data_referencia, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        logger.info(f"Iniciando consolidação para data: {self.data_referencia}")
        
    def notificar_telegram(self, mensagem):
        """Envia notificação no Telegram em caso de erro/sucesso"""
        try:
            # Salvar mensagem em arquivo para o sistema OpenClaw processar
            # A notificação real será feita pelo agente principal
            notif_file = LOG_DIR / f"telegram_notification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(notif_file, 'w') as f:
                f.write(mensagem)
            logger.info(f"Notificação salva em: {notif_file}")
        except Exception as e:
            logger.error(f"Erro ao salvar notificação: {e}")
    
    def carregar_mapeamento(self):
        """Carrega mapeamento Funil -> Produto"""
        mapper_path = Path(__file__).parent / "mappers" / "funil_to_produto.py"
        
        if not mapper_path.exists():
            logger.error(f"Arquivo de mapeamento não encontrado: {mapper_path}")
            self.notificar_telegram(f"⚠️ HULI Consolidator: Arquivo de mapeamento não encontrado! Data: {self.data_referencia}")
            return {}
        
        # Executar o arquivo Python para obter o dicionário
        import importlib.util
        spec = importlib.util.spec_from_file_location("funil_to_produto", mapper_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return getattr(module, 'FUNIL_TO_PRODUTO', {})
    
    def buscar_dados_2ul(self):
        """Busca identificadores 2UL, mapeamento Funil->Produto e identificador de leads da planilha"""
        logger.info("Buscando identificadores 2UL e mapeamentos...")
        try:
            import subprocess
            result = subprocess.run(
                ["gog", "sheets", "get", PLANILHA_2UL_ID, "Página1!A:D", "--json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Erro gog: {result.stderr}")
            
            resposta = json.loads(result.stdout)
            dados = resposta.get('values', [])
            
            if not dados or not isinstance(dados, list):
                logger.error("Formato de dados inválido da planilha 2UL")
                return []
            
            # Ignorar header (primeira linha), retornar lista de (funil, identificador, produto, identificador_leads)
            resultados = []
            for i, row in enumerate(dados):
                if i == 0:  # Pular header
                    continue
                if isinstance(row, list) and len(row) >= 2:
                    funil = row[0] if row[0] else None
                    identificador = row[1] if len(row) > 1 and row[1] else None
                    produto = row[2] if len(row) > 2 and row[2] else None
                    identificador_leads = row[3] if len(row) > 3 and row[3] else None  # Coluna D
                    if funil and identificador:
                        resultados.append((funil, identificador, produto, identificador_leads))
            
            return resultados
            
        except Exception as e:
            logger.error(f"Erro ao buscar identificadores 2UL: {e}")
            self.notificar_telegram(f"🔴 HULI Consolidator: Erro ao buscar identificadores 2UL. Data: {self.data_referencia}")
            return []
    
    def buscar_dados_facebook(self, identificador_2ul):
        """Busca dados do Facebook para um identificador específico"""
        logger.info(f"Buscando dados Facebook para: {identificador_2ul}")
        try:
            import subprocess
            # Buscar todas as linhas da planilha de tráfego
            result = subprocess.run(
                ["gog", "sheets", "get", PLANILHA_TRAFEGO_ID, "Dados!A:Z", "--json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Erro gog: {result.stderr}")
            
            resposta = json.loads(result.stdout)
            dados = resposta.get('values', [])
            
            if not dados:
                logger.warning("Nenhum dado retornado da planilha de tráfego")
                return None
            
            # Filtrar pelo identificador e data
            investimento_total = 0
            impressoes_total = 0
            views_total = 0
            cliques_total = 0
            
            for row in dados[1:]:  # Ignorar header
                if len(row) < 14:  # Precisa até coluna N (Impressões)
                    continue
                    
                # Estrutura correta da planilha:
                # A=Data(0), B=Conta(1), C=Campanha(2)=Identificador 2UL, D=Conjunto(3), E=Anuncio(4)
                # F=Gasto(5), G=Mensagens(6), H=CustoMensagem(7), I=Cliques(8), J=CPC(9)
                # K=LandingPageViews(10), L=CustoLPV(11), M=ConnectRate(12), N=Impressoes(13), O=CPM(14)
                
                row_identificador = row[2] if len(row) > 2 else ""  # Coluna C - Campanha
                row_data = row[0] if len(row) > 0 else ""  # Coluna A - Data
                
                # Debug: mostrar algumas campanhas para verificar
                # logger.debug(f"Verificando - Campanha: '{row_identificador}' vs Identificador: '{identificador_2ul}'")
                
                # Verificar se identificador está na campanha (case-insensitive) e se data corresponde
                identificador_busca = str(identificador_2ul).upper().strip()
                campanha_upper = str(row_identificador).upper().strip()
                
                if identificador_busca in campanha_upper:
                    # Verificar se a data contém o dia de referência (formato: 2026-02-03T00:00:00-03:00)
                    if self.data_referencia not in str(row_data):
                        continue
                    
                    # Log quando encontra correspondência
                    logger.debug(f"✓ Match encontrado: Campanha='{row_identificador}' contém '{identificador_2ul}' | Data={row_data}")
                    
                    # Extrair métricas (converter vírgula para ponto)
                    try:
                        spend_str = str(row[5]).replace(',', '.') if len(row) > 5 and row[5] else '0'  # Coluna F (Gasto)
                        impressoes_str = str(row[13]).replace(',', '.') if len(row) > 13 and row[13] else '0'  # Coluna N (Impressões)
                        views_str = str(row[10]).replace(',', '.') if len(row) > 10 and row[10] else '0'  # Coluna K (Landing Page Views)
                        cliques_str = str(row[8]).replace(',', '.') if len(row) > 8 and row[8] else '0'  # Coluna I (Cliques)
                        
                        spend = float(spend_str)  # Coluna F (Gasto)
                        impressoes = int(float(impressoes_str))  # Coluna N (Impressões)
                        views = int(float(views_str))  # Coluna K (Landing Page Views)
                        cliques = int(float(cliques_str))  # Coluna I (Cliques)
                        
                        investimento_total += spend
                        impressoes_total += impressoes
                        views_total += views
                        cliques_total += cliques
                            
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Erro ao processar linha: {e}")
                        continue
            
            # Calcular Connect Rate: (Views / Cliques) - sem *100 pois a coluna já tem formatação de %
            connect_rate_calculado = 0
            if cliques_total > 0:
                connect_rate_calculado = round((views_total / cliques_total), 4)
            
            # Log dos valores calculados
            logger.info(f"📊 Dados Facebook - Investimento: R$ {investimento_total:.2f}, Impressões: {impressoes_total}, Views: {views_total}, Cliques: {cliques_total}, Connect: {connect_rate_calculado}%")
            
            return {
                'investimento': round(investimento_total, 2),
                'impressoes': impressoes_total,
                'views_pagina': views_total,
                'cliques': cliques_total,
                'connect_rate': connect_rate_calculado
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados Facebook: {e}")
            return None
    
    def buscar_dados_hotmart(self, nome_produto):
        """Busca dados de vendas da Hotmart para um produto"""
        logger.info(f"Buscando dados Hotmart para: {nome_produto}")
        try:
            import subprocess
            result = subprocess.run(
                ["gog", "sheets", "get", PLANILHA_VENDAS_ID, "Vendas!A:P", "--json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Erro gog: {result.stderr}")
            
            resposta = json.loads(result.stdout)
            dados = resposta.get('values', [])
            
            if not dados:
                logger.warning("Nenhum dado retornado da planilha de vendas")
                return None
            
            vendas = []
            vendas_excluidas_drp = 0
            vendas_excluidas_recorrencia = 0
            
            for row in dados[1:]:
                if len(row) < 11:  # Precisa até coluna K (Recurrency_Number)
                    continue
                
                # Colunas: E=Produto(4), C=Data(2), H=Valor_Total(7), G=Codigo_Preco(6), K=Recurrency_Number(10)
                row_produto = row[4] if len(row) > 4 else ""
                row_data = row[2] if len(row) > 2 else ""
                row_valor = row[7] if len(row) > 7 else ""
                row_codigo_preco = row[6] if len(row) > 6 else ""
                row_recorrencia = row[10] if len(row) > 10 else ""
                
                # Verificar se o produto corresponde e se a data contém o dia de referência
                if nome_produto in str(row_produto) and self.data_referencia in str(row_data):
                    
                    # FILTRO 1: Recurrency_Number deve ser "1" ou vazio (primeira compra)
                    # "1" = primeira compra de assinatura
                    # "" (vazio) = produto único (também conta como primeira compra)
                    # > "1" = renovação (excluir)
                    rec_str = str(row_recorrencia).strip()
                    if rec_str and rec_str != "1":
                        vendas_excluidas_recorrencia += 1
                        logger.debug(f"Venda excluída (recorrência != 1): {row_produto} - Rec: {row_recorrencia}")
                        continue
                    
                    # FILTRO 2: Codigo_Preco NÃO pode terminar com "DRP" (parcelamento inteligente)
                    if str(row_codigo_preco).upper().endswith("DRP"):
                        vendas_excluidas_drp += 1
                        logger.debug(f"Venda excluída (DRP): {row_produto} - Código: {row_codigo_preco}")
                        continue
                    
                    # Venda válida - primeira compra real
                    try:
                        # Converter valor (pode ter vírgula como separador decimal)
                        valor_str = str(row_valor).replace(',', '.') if row_valor else '0'
                        valor = float(valor_str)
                        vendas.append(valor)
                        logger.debug(f"Venda válida encontrada: {row_produto} - R$ {valor} (Rec: {row_recorrencia}, Cod: {row_codigo_preco})")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Erro ao converter valor '{row_valor}': {e}")
                        continue
            
            # Log de resumo dos filtros aplicados
            if vendas_excluidas_drp > 0 or vendas_excluidas_recorrencia > 0:
                logger.info(f"Filtros aplicados: {vendas_excluidas_recorrencia} excluídas por recorrência != 1, {vendas_excluidas_drp} excluídas por DRP")
            
            return {
                'quantidade': len(vendas),
                'ticket_medio': round(sum(vendas) / len(vendas), 2) if vendas else 0
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados Hotmart: {e}")
            return None
    
    def carregar_criterios_qualificacao(self, sigla_funil):
        """Carrega critérios de qualificação MQL/SQL da planilha 2UL"""
        try:
            import subprocess
            result = subprocess.run(
                ["gog", "sheets", "get", PLANILHA_2UL_ID, "Página1!A:K", "--json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return None
            
            resposta = json.loads(result.stdout)
            dados = resposta.get('values', [])
            
            for row in dados[1:]:  # Ignorar header
                if len(row) < 6:
                    continue
                
                row_sigla = row[4] if len(row) > 4 else ""  # Coluna E = Sigla
                
                if row_sigla.upper() == sigla_funil.upper():
                    # Extrair critérios das colunas F-K
                    def parse_valor(val):
                        if not val or str(val).strip().upper() in ['N/A', '', '0']:
                            return None
                        try:
                            return float(str(val).replace('.', '').replace(',', '.'))
                        except:
                            return None
                    
                    criterios = {
                        'mql_renda_min': parse_valor(row[5]) if len(row) > 5 else None,
                        'mql_renda_max': parse_valor(row[6]) if len(row) > 6 else None,
                        'mql_patrimonio_min': parse_valor(row[7]) if len(row) > 7 else None,
                        'mql_patrimonio_max': parse_valor(row[8]) if len(row) > 8 else None,
                        'sql_renda_min': parse_valor(row[9]) if len(row) > 9 else None,
                        'sql_patrimonio_min': parse_valor(row[10]) if len(row) > 10 else None
                    }
                    
                    # Verificar se tem pelo menos um critério válido
                    tem_criterio = any(v is not None for v in criterios.values())
                    return criterios if tem_criterio else None
            
            return None
            
        except Exception as e:
            logger.warning(f"Erro ao carregar critérios de qualificação: {e}")
            return None
    
    def extrair_valor_monetario(self, texto):
        """Extrai valor numérico de texto monetário (ex: 'R$ 20.001 a R$ 35.000' -> 27500)"""
        if not texto:
            return None
        
        import re
        texto = str(texto).upper().strip()
        
        # Remover R$
        texto = texto.replace('R$', '').strip()
        
        # Padrão: range "20.001 a 35.000"
        match_range = re.search(r'(\d{1,3}(?:\.\d{3})*)\s*(?:A|À|ATÉ|-)\s*(\d{1,3}(?:\.\d{3})*)', texto)
        if match_range:
            min_val = float(match_range.group(1).replace('.', ''))
            max_val = float(match_range.group(2).replace('.', ''))
            return (min_val + max_val) / 2
        
        # Padrão: "ATÉ 10.000"
        match_max = re.search(r'(?:ATÉ|MENOS\s+DE)\s*(\d{1,3}(?:\.\d{3})*)', texto)
        if match_max:
            return float(match_max.group(1).replace('.', '')) / 2
        
        # Padrão: "ACIMA DE 1.000.000"
        match_min = re.search(r'(?:ACIMA\s+DE|MAIS\s+DE|MAIOR\s+QUE)\s*(\d{1,3}(?:\.\d{3})*)', texto)
        if match_min:
            return float(match_min.group(1).replace('.', ''))
        
        # Número simples
        match_simples = re.search(r'(\d{1,3}(?:\.\d{3})*)', texto)
        if match_simples:
            return float(match_simples.group(1).replace('.', ''))
        
        return None
    
    def classificar_lead(self, renda_texto_k, renda_texto_p, patrimonio_texto, criterios):
        """Classifica um lead como MQL, SQL ou N/A baseado nos critérios
        
        Args:
            renda_texto_k: Texto da coluna K (Média Salarial)
            renda_texto_p: Texto da coluna P (Faixa de renda mensal)
            patrimonio_texto: Texto da coluna L (Patrimônio)
            criterios: Dicionário com critérios de qualificação
        """
        if not criterios:
            return {'mql': False, 'sql': False}
        
        # Extrair valores das DUAS colunas de renda
        renda_valor_k = self.extrair_valor_monetario(renda_texto_k)
        renda_valor_p = self.extrair_valor_monetario(renda_texto_p)
        
        # Usar o MAIOR valor entre as duas colunas de renda
        renda_valor = None
        if renda_valor_k and renda_valor_p:
            renda_valor = max(renda_valor_k, renda_valor_p)
        elif renda_valor_k:
            renda_valor = renda_valor_k
        elif renda_valor_p:
            renda_valor = renda_valor_p
        
        patrimonio_valor = self.extrair_valor_monetario(patrimonio_texto)
        
        is_mql = False
        is_sql = False
        
        # Verificar MQL
        # Por renda
        if criterios.get('mql_renda_min') and criterios.get('mql_renda_max') and renda_valor:
            if criterios['mql_renda_min'] <= renda_valor <= criterios['mql_renda_max']:
                is_mql = True
        # Por patrimônio
        if criterios.get('mql_patrimonio_min') and criterios.get('mql_patrimonio_max') and patrimonio_valor:
            if criterios['mql_patrimonio_min'] <= patrimonio_valor <= criterios['mql_patrimonio_max']:
                is_mql = True
        
        # Verificar SQL
        # Por renda
        if criterios.get('sql_renda_min') and renda_valor:
            if renda_valor >= criterios['sql_renda_min']:
                is_sql = True
        # Por patrimônio
        if criterios.get('sql_patrimonio_min') and patrimonio_valor:
            if patrimonio_valor >= criterios['sql_patrimonio_min']:
                is_sql = True
        
        # NOTA: SQL é um subconjunto de MQL, mas retornamos ambos independentemente
        # A contagem correta será feita na função contar_leads
        
        return {'mql': is_mql, 'sql': is_sql}
    
    def contar_leads(self, identificador_link, sigla_funil=None):
        """Conta leads na planilha de leads que correspondem ao identificador do link na data de referência
        
        Retorna dicionário com: {'total': int, 'mql': int, 'sql': int}
        Se sigla_funil não for fornecida, retorna apenas total (compatibilidade retroativa)
        """
        if not identificador_link:
            logger.info(f"Sem identificador de link para buscar leads")
            return {'total': 0, 'mql': 0, 'sql': 0} if sigla_funil else 0
        
        # Converter data de YYYY-MM-DD para DD/MM/YYYY (formato da planilha de leads)
        try:
            data_obj = datetime.strptime(self.data_referencia, '%Y-%m-%d')
            data_busca = data_obj.strftime('%d/%m/%Y')
        except:
            data_busca = self.data_referencia  # Fallback
        
        logger.info(f"Buscando leads para identificador: {identificador_link} na data: {data_busca}")
        
        # Carregar critérios de qualificação se sigla fornecida
        criterios = None
        if sigla_funil:
            criterios = self.carregar_criterios_qualificacao(sigla_funil)
            if criterios:
                logger.info(f"Critérios de qualificação carregados para {sigla_funil}")
        
        try:
            import subprocess
            # Buscar até coluna P (Faixa de renda mensal) - precisa de K, L e P
            result = subprocess.run(
                ["gog", "sheets", "get", PLANILHA_LEADS_ID, "A:P", "--json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Erro gog: {result.stderr}")
            
            resposta = json.loads(result.stdout)
            dados = resposta.get('values', [])
            
            if not dados:
                logger.warning("Nenhum dado retornado da planilha de leads")
                return {'total': 0, 'mql': 0, 'sql': 0} if sigla_funil else 0
            
            total = 0
            mql_count = 0
            sql_count = 0
            
            for row in dados[1:]:  # Ignorar header
                if len(row) < 10:  # Precisa até coluna J (UTM)
                    continue
                
                # Coluna A = Data, Coluna J = UTM_Página
                row_data = row[0] if len(row) > 0 else ""
                row_utm = row[9] if len(row) > 9 else ""  # Coluna J
                
                # Verificar se a data corresponde e se UTM contém o identificador
                data_str_raw = str(row_data).strip()
                
                # LIMPEZA: Remover hora se presente
                if ',' in data_str_raw:
                    data_str = data_str_raw.split(',')[0].strip()
                else:
                    data_str = data_str_raw
                
                utm_str = str(row_utm).lower()
                
                data_match = data_busca == data_str
                utm_match = identificador_link.lower() in utm_str
                
                if data_match and utm_match:
                    total += 1
                    
                    # Classificar lead se temos critérios
                    if criterios and sigla_funil:
                        renda_texto_k = row[10] if len(row) > 10 else ""  # Coluna K = Média Salarial
                        renda_texto_p = row[15] if len(row) > 15 else ""  # Coluna P = Faixa de renda mensal
                        patrimonio_texto = row[11] if len(row) > 11 else ""  # Coluna L = Patrimônio
                        
                        classificacao = self.classificar_lead(renda_texto_k, renda_texto_p, patrimonio_texto, criterios)
                        
                        if classificacao['sql']:
                            sql_count += 1
                            mql_count += 1  # SQL também é MQL (subconjunto)
                        elif classificacao['mql']:
                            mql_count += 1
                        
                        logger.debug(f"Lead classificado: MQL={classificacao['mql']}, SQL={classificacao['sql']} | Renda K: {renda_texto_k}, Renda P: {renda_texto_p}, Patr: {patrimonio_texto}")
                    
                    logger.info(f"✓ Lead encontrado: Data={data_str}, UTM={row_utm}")
            
            logger.info(f"✓ Leads encontrados: Total={total}, MQL={mql_count}, SQL={sql_count} para identificador '{identificador_link}'")
            
            if sigla_funil:
                return {'total': total, 'mql': mql_count, 'sql': sql_count}
            else:
                return total
            
        except Exception as e:
            logger.error(f"Erro ao buscar leads: {e}")
            return {'total': 0, 'mql': 0, 'sql': 0} if sigla_funil else 0
    
    def inferir_tipo_funil(self, nome_funil):
        """Infere o tipo do funil baseado no nome, ou busca no dia anterior"""
        # Primeiro tenta inferir do nome
        nome_lower = nome_funil.lower()
        
        if 'webinário' in nome_lower or 'webinar' in nome_lower:
            return 'Webinário'
        elif 'vsl' in nome_lower:
            return 'VSL'
        elif 'quiz' in nome_lower or 'questionário' in nome_lower:
            return 'Quiz'
        elif 'aula' in nome_lower:
            return 'Aula ao Vivo'
        elif 'desafio' in nome_lower:
            return 'Desafio'
        elif 'tripwire' in nome_lower or 'mdge' in nome_lower:
            return 'Tripwire'
        
        # Se não conseguir inferir, busca no dia anterior na Planilha HULI
        logger.info(f"Buscando Tipo_Funil do dia anterior para: {nome_funil}")
        try:
            import subprocess
            result = subprocess.run(
                ["gog", "sheets", "get", PLANILHA_HULI_ID, "Acompanhamento diário!A:Z", "--json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                resposta = json.loads(result.stdout)
                dados = resposta.get('values', [])
                for row in dados[1:]:
                    if len(row) >= 3:
                        row_data = row[0] if len(row) > 0 else ""
                        row_funil = row[1] if len(row) > 1 else ""
                        row_tipo = row[2] if len(row) > 2 else ""
                        
                        # Se encontrar o mesmo funil no dia anterior
                        if nome_funil in str(row_funil) and self.data_ontem in str(row_data) and row_tipo:
                            return row_tipo
                            
        except Exception as e:
            logger.warning(f"Erro ao buscar tipo do dia anterior: {e}")
        
        # Fallback
        return 'Desconhecido'
    
    def inserir_na_huli(self, linha_dados):
        """Insere linha na Planilha HULI"""
        logger.info(f"Inserindo dados para: {linha_dados.get('funil', 'N/A')}")
        try:
            import subprocess
            
            # Converter data de YYYY-MM-DD para DD/MM/YYYY
            data_raw = linha_dados['data']
            try:
                data_obj = datetime.strptime(data_raw, '%Y-%m-%d')
                data_formatada = data_obj.strftime('%d/%m/%Y')
            except:
                data_formatada = data_raw  # Fallback se falhar
            
            # Mapeamento das colunas da Planilha HULI:
            # A=Data, B=Funil, C=Tipo_Funil, D=Produto, E=Status, F=Investimento, G=Impressoes, H=CPM, I=CTR, J=Views_Pagina
            # K=Connect_Rate, L=Leads, M=CPL, N=MQLs, O=Custo_MQL, P=Taxa_MQL, Q=SQLs, R=Custo_SQL, S=Taxa_SQL
            # T=Compras, U=Receita, V=Ticket_Medio, W=CPA, X=ROAS, Y=Taxa_Conversao, Z=Visitas_Perfil
            # AA=Seguidores, AB=Custo_Seguidor, AC=OBS_Dia, AD=Variacao_CPL, AE=Variacao_CPA, AF=Variacao_ROAS
            # AG=Alerta, AH=Hipotese, AI=Acao_Recomendada
            
            valores = [
                data_formatada,           # A - Data
                linha_dados['funil'],     # B - Funil
                '',                       # C - Tipo_Funil (vazio)
                '',                       # D - Produto (vazio)
                '',                       # E - Status (vazio)
                linha_dados['investimento'],  # F - Investimento (Facebook)
                linha_dados['impressoes'],    # G - Impressoes (Facebook) - ALTERADO: antes era vazio
                '',                       # H - CPM (vazio) - ALTERADO: antes era CPM
                '',                       # I - CTR (Real) (vazio)
                linha_dados['views_pagina'],  # J - Views_Pagina (Facebook)
                linha_dados['connect_rate'],  # K - Connect_Rate (Calculado: Views/Cliques * 100)
                linha_dados.get('leads', 'N/A'),  # L - Leads (contados da planilha de leads ou N/A)
                '',                       # M - CPL (vazio)
                linha_dados.get('mqls', 'N/A'),   # N - MQLs (contados e classificados)
                '',                       # O - Custo_MQL (vazio)
                '',                       # P - Taxa_MQL (vazio)
                linha_dados.get('sqls', 'N/A'),   # Q - SQLs (contados e classificados)
                '',                       # R - Custo_SQL (vazio)
                '',                       # S - Taxa_SQL (vazio)
                linha_dados['compras'],   # T - Compras (Hotmart)
                '',                       # U - Receita (vazio)
                linha_dados['ticket_medio'],  # V - Ticket_Medio (Hotmart)
                '',                       # W - CPA (vazio)
                '',                       # X - ROAS (vazio)
                '',                       # Y - Taxa_Conversao (vazio)
                '',                       # Z - Visitas_Perfil (vazio)
                '',                       # AA - Seguidores (vazio)
                '',                       # AB - Custo_Seguidor (vazio)
                '',                       # AC - OBS_Dia (vazio)
                '',                       # AD - Variacao_CPL (vazio)
                '',                       # AE - Variacao_CPA (vazio)
                '',                       # AF - Variacao_ROAS (vazio)
                '',                       # AG - Alerta (vazio)
                '',                       # AH - Hipotese (vazio)
                ''                        # AI - Acao_Recomendada (vazio)
            ]
            
            result = subprocess.run(
                ["gog", "sheets", "append", PLANILHA_HULI_ID, "Acompanhamento diário!A:AI", 
                 "--values-json", json.dumps([valores]), "--insert", "INSERT_ROWS"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Erro ao inserir: {result.stderr}")
            
            logger.info(f"✅ Dados inseridos com sucesso para {linha_dados['funil']}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao inserir na HULI: {e}")
            return False
    
    def executar(self):
        """Executa o fluxo completo de consolidação"""
        logger.info("="*60)
        logger.info(f"INICIANDO CONSOLIDAÇÃO HULI - Data: {self.data_referencia}")
        logger.info("="*60)
        
        # 1. Buscar identificadores 2UL (inclui mapeamento Funil->Produto da coluna C)
        funis_2ul = self.buscar_dados_2ul()
        if not funis_2ul:
            logger.error("Nenhum identificador 2UL encontrado!")
            self.notificar_telegram(f"🔴 HULI Consolidator: Nenhum identificador 2UL encontrado! Data: {self.data_referencia}")
            return False
        
        logger.info(f"Encontrados {len(funis_2ul)} funis para processar")
        
        # 2. Processar cada funil
        sucessos = 0
        falhas = 0
        
        for nome_funil, identificador_2ul, nome_produto, identificador_leads in funis_2ul:
            logger.info(f"\n--- Processando: {nome_funil} ---")
            
            # 2.1 Buscar dados Facebook
            dados_fb = self.buscar_dados_facebook(identificador_2ul)
            if not dados_fb:
                logger.warning(f"Sem dados de Facebook para {nome_funil}")
                falhas += 1
                continue
            
            # 2.2 Buscar dados Hotmart (se produto estiver definido)
            dados_hotmart = {'quantidade': 0, 'ticket_medio': 0}
            
            if nome_produto:
                resultado_hotmart = self.buscar_dados_hotmart(nome_produto)
                if resultado_hotmart:
                    dados_hotmart = resultado_hotmart
                    logger.info(f"✓ Vendas encontradas: {dados_hotmart['quantidade']} | Ticket: R$ {dados_hotmart['ticket_medio']}")
                else:
                    logger.warning(f"Produto '{nome_produto}' não encontrado na Hotmart para data {self.data_referencia}")
            else:
                logger.warning(f"Funil '{nome_funil}' sem produto mapeado (coluna C vazia)")
            
            # 2.3 Contar leads (se identificador de link estiver definido)
            # Agora também conta MQLs e SQLs automaticamente
            quantidade_leads = 0
            quantidade_mqls = 0
            quantidade_sqls = 0
            
            if identificador_leads:
                # Extrair sigla do funil (usar identificador_leads como fallback)
                sigla_funil = identificador_leads
                
                # Chamar nova versão que retorna dict com total, mql, sql
                resultado_leads = self.contar_leads(identificador_leads, sigla_funil)
                
                if isinstance(resultado_leads, dict):
                    quantidade_leads = resultado_leads.get('total', 0)
                    quantidade_mqls = resultado_leads.get('mql', 0)
                    quantidade_sqls = resultado_leads.get('sql', 0)
                else:
                    # Fallback para compatibilidade
                    quantidade_leads = resultado_leads
            else:
                logger.info(f"Funil '{nome_funil}' sem identificador de leads (coluna D vazia)")
            
            # 2.4 Inferir tipo do funil
            tipo_funil = self.inferir_tipo_funil(nome_funil)
            
            # 2.5 Montar linha de dados (apenas colunas que serão preenchidas)
            # Se não houver identificador de leads, usar 'N/A'
            leads_valor = quantidade_leads if identificador_leads and identificador_leads != 'N/A' else 'N/A'
            mqls_valor = quantidade_mqls if identificador_leads and identificador_leads != 'N/A' else 'N/A'
            sqls_valor = quantidade_sqls if identificador_leads and identificador_leads != 'N/A' else 'N/A'
            
            linha = {
                'data': self.data_referencia,
                'funil': nome_funil,
                'investimento': dados_fb['investimento'],
                'impressoes': dados_fb['impressoes'],
                'views_pagina': dados_fb['views_pagina'],
                'connect_rate': dados_fb['connect_rate'],
                'leads': leads_valor,
                'mqls': mqls_valor,
                'sqls': sqls_valor,
                'compras': dados_hotmart['quantidade'],
                'ticket_medio': dados_hotmart['ticket_medio']
            }
            
            # 2.6 Inserir na Planilha HULI
            if self.inserir_na_huli(linha):
                sucessos += 1
            else:
                falhas += 1
        
        # 3. Resumo
        logger.info("="*60)
        logger.info(f"CONSOLIDAÇÃO CONCLUÍDA")
        logger.info(f"Sucessos: {sucessos} | Falhas: {falhas}")
        logger.info("="*60)
        
        # Notificar resultado
        if falhas == 0:
            self.notificar_telegram(f"✅ HULI Consolidator: {sucessos} funis processados com sucesso! Data: {self.data_referencia}")
        else:
            self.notificar_telegram(f"⚠️ HULI Consolidator: {sucessos} sucessos, {falhas} falhas. Data: {self.data_referencia}. Verifique logs.")
        
        return falhas == 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Consolida dados na Planilha HULI')
    parser.add_argument('--data', type=str, help='Data de referência (YYYY-MM-DD)')
    args = parser.parse_args()
    
    consolidator = HuliConsolidator(data_referencia=args.data)
    sucesso = consolidator.executar()
    
    sys.exit(0 if sucesso else 1)

#!/usr/bin/env python3
"""
🎯 Script de Análise Diária de Funis - HULI
Segue o roteiro da Rotina do Gestor de Aquisição (rotina-gestor-aquisicao.md)

ETAPA 2: Análises Diárias
- 2.1 Análise Geral da Empresa
- 2.2 Análise por Funil (comparativo dia vs média 7 dias)

Uso:
    python3 analisar_funis.py --data 2026-02-10
    python3 analisar_funis.py  # Usa ontem como padrão
"""

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Importar Google Docs Editor
sys.path.insert(0, str(Path(__file__).parent))
try:
    import google_docs_editor
    GOOGLE_DOCS_AVAILABLE = True
except ImportError as e:
    GOOGLE_DOCS_AVAILABLE = False
    print(f"⚠️  google_docs_editor não disponível - será salvo apenas em arquivo local")
    print(f"   Erro: {e}")

# Configurações
PLANILHA_HULI = "1QAvr_4aNmtJMCGlr_UgFufMuJWStRgkYKs52pxz6xAk"
ABA_HULI = "Acompanhamento Diário"
BRAIN_PATH = Path.home() / "Desktop" / "Brain" / "analises"
# Folder ID para análises de funis no Google Drive
GOOGLE_DRIVE_FOLDER_ID = "1Vth0qFLjX-QJbU9I2fKA4PYa3dxLzE50"
DRIVE_LINK = f"https://drive.google.com/drive/folders/{GOOGLE_DRIVE_FOLDER_ID}"

# Thresholds para alertas
ALERTAS = {
    "cpl_alto": 1.5,      # CPL 50% acima da média
    "cpl_baixo": 0.7,     # CPL 30% abaixo da média
    "leads_queda": 0.5,   # Queda de 50% nos leads
    "leads_alta": 1.5,    # Aumento de 50% nos leads
    "cpa_critico": 100,   # CPA acima de R$ 100
    "investimento_zero": True,  # Investimento = 0
}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Análise Diária de Funis - HULI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    python3 analisar_funis.py --data 2026-02-10
    python3 analisar_funis.py  # Análise de ontem
        """
    )
    parser.add_argument(
        "--data",
        type=str,
        help="Data da análise (formato: YYYY-MM-DD). Padrão: ontem"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(BRAIN_PATH),
        help=f"Pasta de saída. Padrão: {BRAIN_PATH}"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar análise sem salvar arquivo"
    )
    parser.add_argument(
        "--sem-agente",
        action="store_true",
        help="Não chamar o agente de análise inteligente (análise base apenas)"
    )
    return parser.parse_args()


def get_data_analise(data_str=None):
    """Retorna a data da análise (ontem se não especificado)."""
    if data_str:
        return datetime.strptime(data_str, "%Y-%m-%d")
    return datetime.now() - timedelta(days=1)


def formatar_data(data):
    """Formata data para o padrão da planilha HULI (DD/MM/YYYY)."""
    return data.strftime("%d/%m/%Y")


def parse_number(val):
    """Converte valor da planilha para número."""
    if not val or val in ['N/A', '-', '', 'Ativo', 'Desativado']:
        return 0
    try:
        # Remove R$, %, pontos de milhar e troca vírgula por ponto
        cleaned = str(val).replace('R$', '').replace('%', '').strip()
        # Remove pontos de milhar (assumindo que vírgula é decimal)
        if ',' in cleaned and '.' in cleaned:
            # Formato brasileiro: 1.234,56
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            # Pode ser decimal: 1234,56
            cleaned = cleaned.replace(',', '.')
        return float(cleaned)
    except:
        return 0


def buscar_dados_planilha():
    """Busca dados da planilha HULI via gog CLI."""
    print("📊 Buscando dados da Planilha HULI...")
    
    cmd = [
        "gog", "sheets", "get", PLANILHA_HULI,
        f"{ABA_HULI}!A:Z",
        "--json"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"❌ Erro ao buscar dados: {result.stderr}")
            return None
        
        return json.loads(result.stdout)
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


def processar_dados(data_json, data_analise):
    """Processa dados da planilha e retorna estrutura organizada."""
    rows = data_json.get('values', [])
    
    # Gerar lista de 7 dias anteriores
    datas_periodo = []
    for i in range(7, 0, -1):
        dia = data_analise - timedelta(days=i)
        datas_periodo.append(formatar_data(dia))
    
    data_alvo = formatar_data(data_analise)
    
    # Estrutura: funil -> data -> métricas
    dados_funis = defaultdict(lambda: defaultdict(dict))
    
    for row in rows[2:]:  # Pular headers
        if len(row) < 6:
            continue
        
        data_row = row[0] if len(row) > 0 else ''
        funil = row[1] if len(row) > 1 else ''
        
        if not funil:
            continue
        
        # Processar se for a data alvo ou alguma das datas do período
        if data_row == data_alvo or data_row in datas_periodo:
            metricas = {
                'investimento': parse_number(row[5]) if len(row) > 5 else 0,
                'impressoes': parse_number(row[6]) if len(row) > 6 else 0,
                'cpm': parse_number(row[7]) if len(row) > 7 else 0,
                'ctr': parse_number(row[8]) if len(row) > 8 else 0,
                'views': parse_number(row[9]) if len(row) > 9 else 0,
                'connect_rate': parse_number(row[10]) if len(row) > 10 else 0,
                'leads': parse_number(row[11]) if len(row) > 11 else 0,
                'cpl': parse_number(row[12]) if len(row) > 12 else 0,
                'mqls': parse_number(row[13]) if len(row) > 13 else 0,  # Coluna N
                'sqls': parse_number(row[16]) if len(row) > 16 else 0,  # Coluna Q
                'vendas': parse_number(row[19]) if len(row) > 19 else 0,
                'ticket': parse_number(row[21]) if len(row) > 21 else 0,
                'cpa': parse_number(row[22]) if len(row) > 22 else 0,
                'roas': parse_number(row[23]) if len(row) > 23 else 0,
                'tx_conv': parse_number(row[24]) if len(row) > 24 else 0,
            }
            dados_funis[funil][data_row] = metricas
    
    return dados_funis, datas_periodo, data_alvo


def calcular_medias(dados_funil, datas_periodo):
    """Calcula médias dos últimos 7 dias para um funil."""
    medias = {}
    metricas = ['investimento', 'leads', 'mqls', 'sqls', 'cpl', 'vendas', 'cpa', 'connect_rate', 'cpm', 'ctr']
    
    for metrica in metricas:
        valores = [
            dados_funil.get(d, {}).get(metrica, 0)
            for d in datas_periodo
            if d in dados_funil
        ]
        valores = [v for v in valores if v > 0 or metrica in ['leads', 'vendas', 'mqls', 'sqls']]
        medias[metrica] = sum(valores) / len(valores) if valores else 0
    
    return medias


def calcular_variacao(val_atual, val_media):
    """Calcula variação percentual."""
    if val_media == 0:
        return 0
    return ((val_atual - val_media) / val_media) * 100


def get_status_emoji(variacao, metrica):
    """Retorna emoji de status baseado na variação."""
    if metrica in ['cpl', 'cpa']:
        # Para custos: queda é bom, alta é ruim
        if variacao < -30:
            return '🟢'
        elif variacao > 50:
            return '🔴'
        elif variacao > 20:
            return '🟡'
        else:
            return '➡️'
    elif metrica in ['leads', 'vendas']:
        # Para volume: alta é bom, queda é ruim
        if variacao > 50:
            return '🟢'
        elif variacao < -50:
            return '🔴'
        elif variacao < -20:
            return '🟡'
        else:
            return '➡️'
    else:
        return '➡️'


def identificar_alertas(funil, dados_dia, medias):
    """Identifica alertas para um funil."""
    alertas = []
    
    # CPL alto
    if medias.get('cpl', 0) > 0:
        var_cpl = calcular_variacao(dados_dia.get('cpl', 0), medias['cpl'])
        if var_cpl > 50:
            alertas.append(f"🔴 CPL explodiu +{var_cpl:.0f}%")
    
    # Queda brusca de leads
    if medias.get('leads', 0) > 0:
        var_leads = calcular_variacao(dados_dia.get('leads', 0), medias['leads'])
        if var_leads < -50:
            alertas.append(f"🔴 Leads caíram {var_leads:.0f}%")
    
    # CPA crítico
    if dados_dia.get('cpa', 0) > ALERTAS['cpa_critico']:
        alertas.append(f"🟡 CPA crítico: R$ {dados_dia['cpa']:.2f}")
    
    # Alto investimento, zero resultado
    if dados_dia.get('investimento', 0) > 500 and dados_dia.get('vendas', 0) == 0:
        if dados_dia.get('leads', 0) < 5:
            alertas.append("🔴 Alto investimento, baixo retorno")
    
    return alertas


def gerar_evolucao_visual(dados_funil, datas_periodo, data_alvo):
    """Gera representação visual da evolução de leads."""
    todas_datas = datas_periodo + [data_alvo]
    evolucao = []
    
    for d in todas_datas:
        leads = dados_funil.get(d, {}).get('leads', 0)
        data_short = d[:5]  # DD/MM
        evolucao.append(f"{data_short}:{int(leads)}")
    
    return " → ".join(evolucao)


def gerar_analise_geral(dados_funis, datas_periodo, data_alvo):
    """Gera Análise Geral da Empresa (ETAPA 2.1)."""
    
    # Calcular totais
    total_invest_dia = 0
    total_invest_7d = 0
    total_leads_dia = 0
    total_leads_7d = 0
    total_mqls_dia = 0
    total_mqls_7d = 0
    total_sqls_dia = 0
    total_sqls_7d = 0
    total_vendas_dia = 0
    total_vendas_7d = 0
    
    funis_ativos = []
    
    for funil, dados in dados_funis.items():
        dados_dia = dados.get(data_alvo, {})
        medias = calcular_medias(dados, datas_periodo)
        
        if dados_dia.get('investimento', 0) > 0 or dados_dia.get('leads', 0) > 0:
            funis_ativos.append(funil)
        
        total_invest_dia += dados_dia.get('investimento', 0)
        total_leads_dia += dados_dia.get('leads', 0)
        total_mqls_dia += dados_dia.get('mqls', 0)
        total_sqls_dia += dados_dia.get('sqls', 0)
        total_vendas_dia += dados_dia.get('vendas', 0)
        
        total_invest_7d += medias.get('investimento', 0) * 7
        total_leads_7d += medias.get('leads', 0) * 7
        total_mqls_7d += medias.get('mqls', 0) * 7
        total_sqls_7d += medias.get('sqls', 0) * 7
        total_vendas_7d += medias.get('vendas', 0) * 7
    
    media_invest_7d = total_invest_7d / 7 if total_invest_7d > 0 else 0
    media_leads_7d = total_leads_7d / 7 if total_leads_7d > 0 else 0
    media_mqls_7d = total_mqls_7d / 7 if total_mqls_7d > 0 else 0
    media_sqls_7d = total_sqls_7d / 7 if total_sqls_7d > 0 else 0
    media_vendas_7d = total_vendas_7d / 7 if total_vendas_7d > 0 else 0
    
    var_invest = calcular_variacao(total_invest_dia, media_invest_7d)
    var_leads = calcular_variacao(total_leads_dia, media_leads_7d)
    var_mqls = calcular_variacao(total_mqls_dia, media_mqls_7d)
    var_sqls = calcular_variacao(total_sqls_dia, media_sqls_7d)
    var_vendas = calcular_variacao(total_vendas_dia, media_vendas_7d)
    
    # Identificar alertas gerais
    alertas_gerais = []
    destaques = []
    
    for funil, dados in dados_funis.items():
        dados_dia = dados.get(data_alvo, {})
        medias = calcular_medias(dados, datas_periodo)
        alertas_funil = identificar_alertas(funil, dados_dia, medias)
        alertas_gerais.extend([f"{funil}: {a}" for a in alertas_funil])
        
        # Destaques positivos
        if medias.get('cpl', 0) > 0:
            var_cpl = calcular_variacao(dados_dia.get('cpl', 0), medias['cpl'])
            if var_cpl < -30 and dados_dia.get('leads', 0) > 0:
                destaques.append(f"{funil}: CPL caiu {var_cpl:.0f}%")
        
        if dados_dia.get('vendas', 0) > medias.get('vendas', 0) * 2:
            destaques.append(f"{funil}: {int(dados_dia.get('vendas', 0))} vendas (acima da média)")
    
    return {
        'total_invest_dia': total_invest_dia,
        'total_invest_7d': media_invest_7d,
        'var_invest': var_invest,
        'total_leads_dia': total_leads_dia,
        'total_leads_7d': media_leads_7d,
        'var_leads': var_leads,
        'total_mqls_dia': total_mqls_dia,
        'total_mqls_7d': media_mqls_7d,
        'var_mqls': var_mqls,
        'total_sqls_dia': total_sqls_dia,
        'total_sqls_7d': media_sqls_7d,
        'var_sqls': var_sqls,
        'total_vendas_dia': total_vendas_dia,
        'total_vendas_7d': media_vendas_7d,
        'var_vendas': var_vendas,
        'funis_ativos': funis_ativos,
        'alertas': alertas_gerais,
        'destaques': destaques
    }


def gerar_analise_por_funil(dados_funis, datas_periodo, data_alvo):
    """Gera Análise por Funil (ETAPA 2.2)."""
    analises = []
    
    for funil in sorted(dados_funis.keys()):
        dados = dados_funis[funil]
        dados_dia = dados.get(data_alvo, {})
        
        # Pular funis sem dados no dia
        if not dados_dia:
            continue
        
        medias = calcular_medias(dados, datas_periodo)
        
        # Calcular variações
        metricas_var = {}
        for m in ['investimento', 'leads', 'cpl', 'vendas', 'cpa', 'connect_rate', 'cpm']:
            val_dia = dados_dia.get(m, 0)
            val_media = medias.get(m, 0)
            var = calcular_variacao(val_dia, val_media)
            emoji = get_status_emoji(var, m)
            metricas_var[m] = {
                'dia': val_dia,
                'media': val_media,
                'var': var,
                'emoji': emoji
            }
        
        # Evolução visual
        evolucao = gerar_evolucao_visual(dados, datas_periodo, data_alvo)
        
        # Alertas
        alertas = identificar_alertas(funil, dados_dia, medias)
        
        # Classificar status do funil
        if any('🔴' in a for a in alertas):
            status_funil = '🔴 CRÍTICO'
        elif any('🟡' in a for a in alertas):
            status_funil = '🟡 ATENÇÃO'
        elif metricas_var.get('cpl', {}).get('var', 0) < -20:
            status_funil = '🟢 MELHORANDO'
        else:
            status_funil = '➡️ ESTÁVEL'
        
        analises.append({
            'funil': funil,
            'metricas': metricas_var,
            'evolucao': evolucao,
            'alertas': alertas,
            'status': status_funil,
            'dados_dia': dados_dia,
            'medias': medias
        })
    
    return analises


def gerar_markdown(data_analise, analise_geral, analises_funis, datas_periodo, data_alvo_str):
    """Gera o documento Markdown completo."""
    
    data_formatada = data_analise.strftime("%d/%m/%Y")
    inicio_periodo = datetime.strptime(datas_periodo[0], "%d/%m/%Y").strftime("%d/%m")
    fim_periodo = datetime.strptime(datas_periodo[-1], "%d/%m/%Y").strftime("%d/%m")
    
    md = f"""# 📊 Análise Diária de Funis - HULI

> **Data da Análise:** {datetime.now().strftime("%d/%m/%Y %H:%M")}  
> **Dia Analisado:** {data_formatada}  
> **Período de Referência:** {inicio_periodo} a {fim_periodo} (7 dias)  
> **Analista:** Margot 🤖  
> **Roteiro:** [Rotina Gestor de Aquisição](../../processos/rotina-gestor-aquisicao.md)

---

## 📋 ANÁLISE GERAL DA EMPRESA (ETAPA 2.1)

### 🎯 Panorama Geral

| Indicador | Dia Analisado | Média 7 Dias | Variação | Tendência |
|-----------|---------------|--------------|----------|-----------|
"""
    
    # Investimento
    emoji_inv = '📈' if analise_geral['var_invest'] > 10 else '📉' if analise_geral['var_invest'] < -10 else '➡️'
    md += f"| 💰 Investimento Total | R$ {analise_geral['total_invest_dia']:,.2f} | R$ {analise_geral['total_invest_7d']:,.2f} | {analise_geral['var_invest']:+.1f}% | {emoji_inv} |\n"
    
    # Leads
    emoji_leads = '📈' if analise_geral['var_leads'] > 10 else '📉' if analise_geral['var_leads'] < -10 else '➡️'
    md += f"| 👥 Total de Leads | {int(analise_geral['total_leads_dia'])} | {int(analise_geral['total_leads_7d'])} | {analise_geral['var_leads']:+.1f}% | {emoji_leads} |\n"
    
    # MQLs
    emoji_mqls = '📈' if analise_geral['var_mqls'] > 10 else '📉' if analise_geral['var_mqls'] < -10 else '➡️'
    md += f"| 🟡 Total MQLs | {int(analise_geral['total_mqls_dia'])} | {int(analise_geral['total_mqls_7d'])} | {analise_geral['var_mqls']:+.1f}% | {emoji_mqls} |\n"
    
    # SQLs
    emoji_sqls = '📈' if analise_geral['var_sqls'] > 10 else '📉' if analise_geral['var_sqls'] < -10 else '➡️'
    md += f"| 🟢 Total SQLs | {int(analise_geral['total_sqls_dia'])} | {int(analise_geral['total_sqls_7d'])} | {analise_geral['var_sqls']:+.1f}% | {emoji_sqls} |\n"
    
    # Vendas
    emoji_vendas = '🚀' if analise_geral['var_vendas'] > 50 else '📈' if analise_geral['var_vendas'] > 10 else '📉' if analise_geral['var_vendas'] < -10 else '➡️'
    md += f"| 🛒 Total de Vendas | {int(analise_geral['total_vendas_dia'])} | {int(analise_geral['total_vendas_7d'])} | {analise_geral['var_vendas']:+.1f}% | {emoji_vendas} |\n"
    
    # Funis ativos
    md += f"| 📊 Funis Ativos | {len(analise_geral['funis_ativos'])} | - | - | - |\n"
    
    # Alertas
    md += "\n### 🚨 Alertas do Dia\n\n"
    if analise_geral['alertas']:
        for alerta in analise_geral['alertas'][:5]:  # Top 5 alertas
            md += f"- {alerta}\n"
    else:
        md += "- Nenhum alerta crítico identificado. ✅\n"
    
    # Destaques
    md += "\n### ⭐ Destaques Positivos\n\n"
    if analise_geral['destaques']:
        for destaque in analise_geral['destaques']:
            md += f"- {destaque}\n"
    else:
        md += "- Nenhum destaque especial no dia.\n"
    
    # Análise por Funil
    md += f"\n---\n\n## 🔍 ANÁLISE POR FUNIL (ETAPA 2.2)\n"
    md += f"*Comparativo: {data_formatada} vs Média dos últimos 7 dias*\n"
    
    for i, analise in enumerate(analises_funis, 1):
        md += f"\n---\n\n### {i}️⃣ {analise['funil']} {analise['status']}\n\n"
        
        # Tabela comparativa
        md += "**📊 Comparativo Dia vs Média 7 Dias:**\n\n"
        md += "| Métrica | Dia Analisado | Média 7D | Variação | Status |\n"
        md += "|---------|---------------|----------|----------|--------|\n"
        
        for metrica, valores in analise['metricas'].items():
            nome_display = {
                'investimento': '💰 Investimento',
                'leads': '👥 Leads',
                'mqls': '🟡 MQLs',
                'sqls': '🟢 SQLs',
                'cpl': '🎯 CPL',
                'vendas': '🛒 Vendas',
                'cpa': '💸 CPA',
                'connect_rate': '📈 Connect Rate',
                'cpm': '👀 CPM'
            }.get(metrica, metrica)
            
            if metrica in ['investimento', 'cpl', 'cpa', 'cpm']:
                val_dia_str = f"R$ {valores['dia']:,.2f}" if valores['dia'] > 0 else "R$ 0,00"
                val_media_str = f"R$ {valores['media']:,.2f}" if valores['media'] > 0 else "R$ 0,00"
            elif metrica == 'connect_rate':
                val_dia_str = f"{valores['dia']:.2f}%"
                val_media_str = f"{valores['media']:.2f}%"
            else:
                val_dia_str = f"{int(valores['dia'])}"
                val_media_str = f"{valores['media']:.1f}"
            
            var_str = f"{valores['var']:+.1f}%"
            
            md += f"| {nome_display} | {val_dia_str} | {val_media_str} | {var_str} | {valores['emoji']} |\n"
        
        # Evolução
        md += f"\n**📉 Evolução de Leads (últimos 7 dias):**\n"
        md += f"```\n{analise['evolucao']}\n```\n"
        
        # Alertas específicos
        if analise['alertas']:
            md += "\n**⚠️ Alertas:**\n"
            for alerta in analise['alertas']:
                md += f"- {alerta}\n"
        
        # Espaço para hipóteses manuais
        md += """
**🧠 Hipóteses para o Resultado:**

1. **[ADICIONAR HIPÓTESE]**
   - *Justificativa:* 
   - *Indicadores que apoiam:* 

2. **[ADICIONAR HIPÓTESE]**
   - *Justificativa:* 
   - *Indicadores que apoiam:* 

**💡 Sugestões de Otimização:**

**🔴 Imediato (Próximas 24h):**
- [ ] 

**🟡 Curto Prazo (Esta semana):**
- [ ] 

**🟢 Médio Prazo (Próximas 2 semanas):**
- [ ] 

"""
    
    # Rodapé
    md += f"""---

## 📁 Links de Referência

- 📊 [Planilha HULI - Acompanhamento Diário](https://docs.google.com/spreadsheets/d/{PLANILHA_HULI}/edit)
- 📈 [Dados de Tráfego - Facebook](https://docs.google.com/spreadsheets/d/1eHHqpErnVaodZhgyHQSg-PjXv4Z8Et6u9dabpODyLr0/edit)
- 🛒 [Todas as Vendas - Hotmart](https://docs.google.com/spreadsheets/d/1WIddZ96vTvaZ9engZuP4L3DOlPhiUoWpz_RWu0oG_0U/edit)
- 📋 [Identificadores 2UL](https://docs.google.com/spreadsheets/d/1zp9b345wFXzwfHJJVZqvnl-cRc3yZqfoUgnLhiZzhuw/edit)
- 📁 [Drive de Análises]({DRIVE_LINK})

---

*Análise gerada automaticamente via `analisar_funis.py`*  
*Template baseado na [Rotina do Gestor de Aquisição](../../processos/rotina-gestor-aquisicao.md)*
"""
    
    return md


def salvar_arquivo(conteudo, data_analise, output_path):
    """Salva o arquivo de análise - tenta Google Docs primeiro, fallback para local."""

    data_formatada = data_analise.strftime("%d/%m/%Y")
    titulo_doc = f"📊 Análise de Funis - {data_formatada}"

    # Tentar salvar no Google Docs
    if GOOGLE_DOCS_AVAILABLE:
        try:
            print(f"\n📤 Salvando análise no Google Docs...")
            doc_id, doc_url = google_docs_editor.create_document(
                title=titulo_doc,
                content_html=conteudo,
                folder_id=GOOGLE_DRIVE_FOLDER_ID
            )

            if doc_id:
                print(f"✅ Documento criado no Google Drive!")
                print(f"🔗 Acesse em: {doc_url}")
                return doc_url
        except Exception as e:
            print(f"⚠️  Erro ao salvar no Google Docs: {e}")
            print("💾 Salvando em arquivo local como fallback...")

    # Fallback: salvar arquivo local
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    nome_arquivo = f"analise-funis-{data_analise.strftime('%Y-%m-%d')}.md"
    caminho_arquivo = output_dir / nome_arquivo

    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)

    print(f"💾 Arquivo salvo localmente em: {caminho_arquivo}")
    return str(caminho_arquivo)


def notificar_erro_telegram(mensagem_erro, data_analise):
    """Envia notificação de erro no Telegram."""
    try:
        import subprocess
        # Usar o message tool do OpenClaw se disponível
        # Fallback: salvar em arquivo para notificação manual
        erro_file = Path.home() / ".openclaw" / "notifications" / f"erro_analise_{data_analise.strftime('%Y%m%d_%H%M%S')}.txt"
        erro_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(erro_file, 'w', encoding='utf-8') as f:
            f.write(f"ERRO NA ANÁLISE HULI - {data_analise.strftime('%d/%m/%Y')}\n")
            f.write("="*60 + "\n")
            f.write(mensagem_erro + "\n")
        
        print(f"   📝 Erro registrado em: {erro_file}")
    except Exception as e:
        print(f"   ❌ Falha ao registrar erro: {e}")


def main():
    """Função principal."""
    args = parse_args()

    # Determinar data da análise
    data_analise = get_data_analise(args.data)
    erro_acumulado = []

    print(f"🎯 Analisando dados de: {formatar_data(data_analise)}")

    # Buscar dados da planilha
    data_json = buscar_dados_planilha()
    if not data_json:
        erro_msg = "❌ Falha ao buscar dados da planilha HULI"
        print(erro_msg)
        notificar_erro_telegram(erro_msg, data_analise)
        sys.exit(1)

    # Processar dados
    try:
        dados_funis, datas_periodo, data_alvo = processar_dados(data_json, data_analise)

        if not dados_funis:
            erro_msg = f"❌ Nenhum dado encontrado para a data: {formatar_data(data_analise)}"
            print(erro_msg)
            notificar_erro_telegram(erro_msg, data_analise)
            sys.exit(1)
    except Exception as e:
        erro_msg = f"❌ Erro ao processar dados: {str(e)}"
        print(erro_msg)
        notificar_erro_telegram(erro_msg, data_analise)
        sys.exit(1)

    print(f"📊 {len(dados_funis)} funis encontrados")

    # Gerar análises
    print("📝 Gerando Análise Geral da Empresa (ETAPA 2.1)...")
    analise_geral = gerar_analise_geral(dados_funis, datas_periodo, data_alvo)

    print("📝 Gerando Análise por Funil (ETAPA 2.2)...")
    analises_funis = gerar_analise_por_funil(dados_funis, datas_periodo, data_alvo)

    # Gerar markdown
    print("📄 Gerando documento...")
    conteudo = gerar_markdown(data_analise, analise_geral, analises_funis, datas_periodo, data_alvo)

    if args.dry_run:
        print("\n" + "="*80)
        print("PREVIEW (dry-run - não será salvo):")
        print("="*80)
        print(conteudo[:2000] + "..." if len(conteudo) > 2000 else conteudo)
        print("="*80)
    else:
        # Salvar arquivo (Google Docs ou local)
        localizacao = salvar_arquivo(conteudo, data_analise, args.output)

        # Resumo
        print("\n📋 RESUMO DA ANÁLISE:")
        print(f"   💰 Investimento Total: R$ {analise_geral['total_invest_dia']:,.2f}")
        print(f"   👥 Total de Leads: {int(analise_geral['total_leads_dia'])}")
        print(f"   🟡 Total MQLs: {int(analise_geral['total_mqls_dia'])}")
        print(f"   🟢 Total SQLs: {int(analise_geral['total_sqls_dia'])}")
        print(f"   🛒 Total de Vendas: {int(analise_geral['total_vendas_dia'])}")
        print(f"   📊 Funis Ativos: {len(analise_geral['funis_ativos'])}")

        if analise_geral['alertas']:
            print(f"\n🚨 Alertas identificados: {len(analise_geral['alertas'])}")
            for alerta in analise_geral['alertas'][:3]:
                print(f"   - {alerta}")

        print(f"\n✅ Análise concluída com sucesso!")


if __name__ == "__main__":
    main()

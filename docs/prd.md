# PRD: Huli Automations Hub - Mission Control

**Versão:** 1.0 - MVP
**Data:** 2026-02-20
**Status:** Ready for Development
**Roadmap:** 3 Fases

---

## 🎯 Visão Estratégica

**Objetivo Principal:**
Centralizar todas as automatizações, Cron Jobs e agentes de IA da empresa Huli em um único hub de controle, eliminando tarefas manuais repetitivas e permitindo inteligência automática na análise de dados.

**Métrica de Sucesso:**
Tempo economizado pela equipe (horas/dia) através de automações crescentes.

**Benefício Comercial:**
- ⏱️ Eliminação de 2-3h/dia de tarefas manuais (extrações + consolidações)
- 📊 Análises automáticas dos funis (tendências, problemas, soluções)
- 🚀 Escala de automações conforme empresa cresce

---

## 📋 Contexto da Empresa

**Huli - Educação em Finanças & Investimentos**

Produtos/Funis:
- 🎓 Treinamentos
- 👥 Mentorias
- 👤 Acompanhamentos Individuais
- 👥 Acompanhamentos em Grupo

**Dados Coletados Diariamente:**
- 💰 Vendas Hotmart (6:00 AM)
- 📱 Tráfego Facebook Ads (6:15 AM)
- 🔗 Consolidação de dados (6:45 AM)
- 📈 Análises semanais de funis (Quarta 7:00 AM)

**Stack Atual:**
- Backend: Python 3.x
- APIs: Hotmart, Facebook Ads, Google Drive/Sheets
- Orquestração: OpenClaw (sistema de agentes)
- CLI: `gog` para Google Sheets

---

## 🏗️ FASE 1: MVP - Mission Control Básico (SEM OpenClaw)

### Escopo MVP

Objetivo: **Dashboard funcional com orquestrador próprio de Cron Jobs - SEM dependência OpenClaw**

#### Features (In Scope):

```
✅ Scheduler próprio:
   - Agendador independente (APScheduler)
   - 4 jobs com horários definidos
   - Executa scripts automaticamente
   - SEM dependência OpenClaw

✅ Dashboard simples com:
   - Lista de Cron Jobs (4 jobs)
   - Status de cada job (Próxima execução, Última execução)
   - Timestamp da última execução
   - Resultado (sucesso/erro)
   - Botão "Executar Agora" para cada job
   - Visualizador de logs

✅ Backend:
   - FastAPI com scheduler integrado
   - API para listar jobs
   - API para disparar job manualmente
   - Logging estruturado (arquivo + console)
   - Health check endpoint

✅ Frontend básico:
   - HTML/CSS simples
   - JavaScript vanilla para updates em tempo real
   - Responsivo (mobile ok)
   - Refresh automático a cada 30s

✅ Scripts rodando SEM mudanças fundamentais:
   - hotmart_to_sheets.py (6:00 AM)
   - facebook_ads_to_sheets.py (6:15 AM)
   - huli_consolidator.py (6:45 AM)
   - Logs salvos localmente e visualizáveis no dashboard

✅ Sistema de Logging:
   - Arquivo de log por job (JSON estruturado)
   - Histórico de 100 últimas execuções por job
   - Status: SUCCESS, ERROR, RUNNING
   - Timestamps precisos
```

#### Out of Scope (Phase 2+):

```
❌ Banco de dados centralizado (Supabase)
❌ Histórico persistente (>100 execuções)
❌ Notificações (Telegram, Email, Slack)
❌ Seção de Agentes de IA
❌ Kanban de Tarefas
❌ Análises inteligentes
❌ Autenticação complexa
❌ Dependência OpenClaw
```

### Tech Stack MVP

- **Backend:** Python 3.8+ (FastAPI + APScheduler)
- **Frontend:** HTML/CSS/JS vanilla
- **Scheduling:** APScheduler (agendador local)
- **Logging:** Python logging + JSON estruturado
- **Database:** JSON files (temporary, Phase 2 = Supabase)
- **Deployment:** Localhost:8000 (pode usar supervisor/systemd depois)

### Deliverables MVP

```
📁 huli-automations-hub/
├── backend/
│   ├── app.py (FastAPI + APScheduler)
│   ├── scheduler/
│   │   ├── __init__.py
│   │   ├── job_scheduler.py
│   │   └── job_executor.py
│   ├── api/
│   │   ├── jobs.py (routes)
│   │   └── logs.py (routes)
│   ├── models/
│   │   └── job.py (Job class)
│   ├── services/
│   │   ├── execution_service.py (executar scripts)
│   │   └── logging_service.py (log estruturado)
│   ├── config.py (configuração jobs)
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── jobs/ (scripts dos jobs)
│   ├── hotmart_to_sheets.py
│   ├── facebook_ads_to_sheets.py
│   └── huli_consolidator.py
├── logs/
│   ├── hotmart_*.json
│   ├── facebook_*.json
│   └── consolidator_*.json
├── config/
│   └── jobs_config.json
└── README.md
```

---

## 📊 FASE 2: Mission Control Completo (Semana 2)

### Adicionar:

```
✅ Banco de dados (Supabase PostgreSQL):
   - Histórico de execuções
   - Dados coletados (Hotmart, FB, etc)
   - Logs estruturados

✅ Dashboard completo:
   - Gráficos de execução (sucesso/erro %)
   - Histórico de 30 dias
   - Alertas de falhas

✅ Seção Skills & Ferramentas:
   - Catálogo de skills disponíveis
   - Status de conexão (Google, Hotmart, FB)
   - Documentação de cada skill

✅ Integração com 3º Cron Job:
   - analisar_funis.py integrado
   - Alertas automáticos (CPL ↑, Leads ↓, etc)
```

---

## 🤖 FASE 3: Agentes de IA Inteligentes (Semana 3+)

### Agentes Esperados:

```
🔍 Agente de Análise:
   - Analisa dados coletados
   - Identifica tendências (quedas de leads)
   - Diagnostica causa (anúncios vs tráfego)

🛠️ Agente de Resolução:
   - Cria plano de ação
   - Gera materiais (copies, designs, etc)
   - Pronto para equipe implementar

📋 Agente de Kanban:
   - Cria tarefas automaticamente
   - Atualiza status em tempo real
   - Notificações de progresso
```

---

## 🔧 Detalhes Técnicos - MVP

### 4 Cron Jobs Agendados (via APScheduler)

| Job | Schedule | Script | Tipo |
|-----|----------|--------|------|
| Facebook Ads | 6:00 AM | `facebook_ads_to_sheets.py` | Daily |
| Hotmart | 6:15 AM | `hotmart_to_sheets.py` | Daily |
| Consolidador | 6:45 AM | `huli_consolidator.py` | Daily |
| Análise Semanal | Quarta 7:00 AM | `analisar_funis.py` | Weekly |

**Cada job:**
- Agendado via APScheduler (não OpenClaw)
- Executa script Python
- Captura stdout/stderr
- Salva log estruturado (JSON)
- Status: SUCCESS ou ERROR
- Timestamp preciso

**Fluxo de execução:**
```
APScheduler detecta hora
    ↓
Dispara execution_service.run_job()
    ↓
Executa subprocess (script Python)
    ↓
Captura saída e tempo de execução
    ↓
Salva log JSON
    ↓
Dashboard atualiza status
```

### APIs Usadas (SEM OpenClaw)

```
📍 Hotmart API (hotmart_python lib)
📍 Facebook Ads API (requests)
📍 Google Sheets API (gog CLI ou google-api-python-client)
📍 SEM Telegram (você acompanha pelo dashboard)
```

### Dependências MVP

```python
# Backend
fastapi==0.104.1
uvicorn==0.24.0
apscheduler==3.10.4  # Scheduler próprio
python-dotenv==1.0.0
requests==2.31.0

# Custom
hotmart_python==latest  # Seu módulo

# Optional (Phase 2)
# google-api-python-client==2.100.0
# gog CLI (já instalado em /opt/homebrew/bin/gog)
```

---

## 🎬 Roadmap de Implementação

### Sprint 1 (HOJE): MVP
- [ ] Setup FastAPI backend
- [ ] Dashboard HTML/CSS
- [ ] Job listing API
- [ ] Execute job endpoint
- [ ] Log viewer
- [ ] Deploy local
- [ ] ✅ Scripts rodando sem mudanças

### Sprint 2: Full Mission Control
- [ ] Supabase setup
- [ ] Database migrations
- [ ] History visualization
- [ ] Skills catalog
- [ ] Alerting system

### Sprint 3: Agents Phase
- [ ] Agent framework integration
- [ ] Analysis agent
- [ ] Resolution agent
- [ ] Kanban sync

---

## 🚨 Riscos & Mitigação

| Risco | Impacto | Mitigação |
|-------|--------|-----------|
| Job falha silenciosamente | Alto | Logging estruturado + Dashboard mostra status |
| Horário UTC vs Local | Médio | APScheduler com timezone Brasil (America/Sao_Paulo) |
| Scripts com bugs | Médio | Try/catch no executor, logs detalhados |
| Credenciais em .env | Médio | Arquivo .env no .gitignore, docs para setup |
| Sem redundância/backup | Alto | Phase 2: Supabase (backup central) |
| Performance com volume | Médio | Phase 3: Otimizações, cache |

---

## 📦 Skills Necessários (Implementar)

### Skill: Google Drive & Sheets Adapter
```
Objetivo: Abstrair dependência do gog CLI
Responsável: @dev (Phase 2)
Integra: Google Drive, Sheets, Docs
Status: Currently via gog CLI → Need proprietary skill
```

### Skill: Hotmart Extractor
```
Objetivo: Encapsular lógica de extração Hotmart
Responsável: @dev
Integra: Hotmart API
Dependência: hotmart_python library
Status: Pronto, apenas refatorar
```

### Skill: Facebook Ads Extractor
```
Objetivo: Encapsular lógica de extração FB Ads
Responsável: @dev
Integra: Facebook Ads API, KPI calculations
Status: Pronto, apenas refatorar
```

---

## 💾 Dados Coletados Diariamente

**Hotmart Sales** (Diário, 6:00 AM)
- ID transação, status, datas
- Produto, preço, método pagamento
- Comprador, email, produtor
- Sales source (tracking)
- ~50-200 vendas/dia

**Facebook Ads** (Diário, 6:15 AM)
- Spend, impressões, alcance
- Cliques, conversões, mensagens
- CPM, CPC, Connect Rate
- Por campanha/anúncio
- 5 contas monitoradas

**Consolidação** (Diário, 6:45 AM)
- Agrega Hotmart + FB Ads
- Calcula KPIs por funil
- Investimento vs Resultado

---

## 📊 Success Metrics

### MVP
- ✅ Dashboard acessível (localhost:8000)
- ✅ 4 jobs listados com status
- ✅ Manual trigger funciona
- ✅ Logs salvos e visualizáveis
- ✅ Scripts rodando sem interrução

### Phase 2
- ⏱️ Time saved: 2h/dia (automatizações)
- 📊 Data quality: 100% (centralizado)
- 🎯 Uptime: >99%

### Phase 3
- 🤖 Agent accuracy: >85%
- 🚀 Problem detection: <1h
- 📈 ROI improvement visible

---

## 🛠️ Especialistas Necessários

| Fase | Especialista | Tarefas |
|------|-------------|---------|
| MVP | @dev | Backend/Frontend/Integration |
| MVP | Você | Validação & ajustes |
| Phase 2 | @architect | Stack decisão (DB, caching) |
| Phase 2 | @data-engineer | Schema Supabase |
| Phase 3 | @ai-specialist | Agent framework |

---

## ⏰ Timeline Estimado

- **MVP (Sem OpenClaw, sem Telegram):** 6-8 horas de desenvolvimento
  - 2h: Estrutura FastAPI + APScheduler
  - 2h: APIs (listar jobs, executar, logs)
  - 2h: Frontend dashboard
  - 1h: Integração & testes
  - 1h: Deploy local

- **Phase 2 (Week 2):** 2-3 dias (Supabase, histórico, alertas)
- **Phase 3 (Week 3+):** Conforme complexidade (Agentes)

---

## 📝 Notas Importantes

1. **Você é solo:** MVP deve ser simples, sem over-engineering
2. **Scripts já funcionam:** Apenas integrar ao dashboard
3. **OpenClaw já orquestra:** Só ler status e logar
4. **Credenciais seguras:** Usar .env (hoje), Supabase secrets (Phase 2)
5. **Escalabilidade:** Supabase permite crescimento sem reescrita

---

## 🚀 Próximos Passos (Immediate)

1. **✅ Confirm architecture:**
   - APScheduler para scheduling? ✅ Aprovado
   - SEM OpenClaw? ✅ Aprovado
   - SEM Telegram? ✅ Aprovado
   - FastAPI + vanilla JS? ✅ Aprovado

2. **Setup do projeto:**
   - `mkdir huli-automations-hub && cd huli-automations-hub`
   - `git init` (ou clone do repo existente)
   - `python -m venv venv && source venv/bin/activate`
   - `pip install -r requirements.txt`

3. **Assign development:**
   - Você quer implementar sozinho?
   - Ou prefere que @dev assuma?

4. **Estruturar código:**
   - Criar árvore de diretórios
   - Copiar scripts para jobs/
   - Criar scheduler base

5. **Deploy local:**
   - `python main.py`
   - Acessar `http://localhost:8000`
   - Testar um job manualmente

---

*PRD Gerado por Morgan (PM) - 2026-02-20*
*Pronto para desenvolvimento no AIOS*

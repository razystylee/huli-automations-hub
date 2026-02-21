# DEV BRIEFING: Huli Automations Hub - MVP Implementation

**Status:** Ready for Development
**Assigned to:** @dev
**Timeline:** 6-8 hours
**Priority:** High

---

## 🎯 O Que Você Precisa Construir

**Huli Automations Hub Mission Control** - Um dashboard que orquestra e monitora 4 Cron Jobs Python que extraem dados de Hotmart, Facebook Ads e consolidam informações.

**TL;DR:**
- FastAPI backend com scheduler integrado (APScheduler)
- Dashboard simples (HTML/CSS/JS)
- Executa 4 scripts Python em horários específicos
- Mostra status, logs e permite trigger manual
- SEM dependência OpenClaw, SEM Telegram

---

## 📋 Escopo MVP

### Deve Ter (In Scope)

```
✅ FastAPI backend com 4 endpoints:
   - GET /api/jobs → lista todos os jobs
   - GET /api/jobs/{id}/logs → logs de um job
   - POST /api/jobs/{id}/execute → dispara job agora
   - GET /health → health check

✅ APScheduler integrado:
   - 6:00 AM: facebook_ads_to_sheets.py
   - 6:15 AM: hotmart_to_sheets.py
   - 6:45 AM: huli_consolidator.py
   - Quarta 7h: analisar_funis.py

✅ Execution Service:
   - Executa scripts via subprocess
   - Captura stdout/stderr
   - Registra tempo de execução
   - Status: SUCCESS ou ERROR

✅ Logging estruturado:
   - JSON format
   - Arquivo por job (hotmart_*.json, facebook_*.json, etc)
   - Histórico de 100 últimas execuções por job
   - Timestamps precisos

✅ Frontend dashboard:
   - Lista jobs com próxima execução
   - Mostra último resultado (✅ ou ❌)
   - Botão "Execute Now" para cada job
   - Visualizador de logs (scrollable)
   - Auto-refresh a cada 30s
   - Simples, não precisa de framework pesado

✅ Tratamento de erros:
   - Job com erro não para o scheduler
   - Captura stack trace
   - Mostra erro no dashboard
```

### Não Precisa (Out of Scope)

```
❌ Banco de dados (use JSON files)
❌ Autenticação/Login
❌ Notificações (Telegram, Email, Slack)
❌ Histórico persistente (>100 execuções)
❌ Integração OpenClaw
❌ Dockerização (pode depois)
```

---

## 🔧 Stack Técnico

### Backend
```
Framework:     FastAPI 0.104.1
Server:        Uvicorn
Scheduler:     APScheduler 3.10.4
Config:        Python-dotenv
HTTP:          Requests
```

### Frontend
```
HTML:          Vanilla HTML5
CSS:           Vanilla CSS3
JS:            Vanilla JavaScript (no framework)
Refresh:       fetch() com setInterval()
```

### Environment
```
Python:        3.8+
OS:            macOS (scripts já em local)
Timezone:      America/Sao_Paulo (IMPORTANTE!)
```

---

## 📂 Estrutura Esperada

```
huli-automations-hub/
│
├── backend/
│   ├── main.py                 # Entry point (FastAPI + APScheduler)
│   │
│   ├── scheduler/
│   │   ├── __init__.py
│   │   ├── job_scheduler.py    # Configura scheduler + jobs
│   │   └── job_executor.py     # Executa scripts
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── jobs.py             # GET /api/jobs
│   │   └── logs.py             # GET /api/jobs/{id}/logs
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── execution_service.py # Executa subprocess
│   │   └── logging_service.py   # Salva logs JSON
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── job.py              # Job dataclass/model
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuração geral
│   │   └── jobs_config.json    # Jobs config (horários)
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── index.html              # Dashboard UI
│   ├── style.css               # Styling
│   └── app.js                  # Refresh logic
│
├── jobs/                        # Scripts Python (copiar para cá)
│   ├── hotmart_to_sheets.py
│   ├── facebook_ads_to_sheets.py
│   ├── huli_consolidator.py
│   └── analisar_funis.py
│
├── logs/                        # Logs de execução (criado automaticamente)
│   ├── hotmart_2026-02-20.json
│   ├── facebook_2026-02-20.json
│   └── ...
│
├── README.md
├── .gitignore
└── Makefile (opcional)
```

---

## 🔌 Jobs Configuration (jobs_config.json)

```json
{
  "jobs": [
    {
      "id": "facebook-ads",
      "name": "Facebook Ads Daily Extraction",
      "script": "jobs/facebook_ads_to_sheets.py",
      "schedule": "0 6 * * *",  // 6:00 AM todos os dias
      "timeout": 300,
      "retries": 0
    },
    {
      "id": "hotmart",
      "name": "Hotmart Daily Sales",
      "script": "jobs/hotmart_to_sheets.py",
      "schedule": "15 6 * * *",  // 6:15 AM
      "timeout": 180,
      "retries": 0
    },
    {
      "id": "consolidator",
      "name": "HULI Consolidator",
      "script": "jobs/huli_consolidator.py",
      "schedule": "45 6 * * *",  // 6:45 AM
      "timeout": 300,
      "retries": 0
    },
    {
      "id": "analise-funis",
      "name": "Análise Semanal de Funis",
      "script": "jobs/analisar_funis.py",
      "schedule": "0 7 * * 3",  // Quarta-feira 7:00 AM
      "timeout": 900,
      "retries": 0
    }
  ]
}
```

---

## 📝 API Endpoints Esperados

### GET /api/jobs
**Response:**
```json
{
  "jobs": [
    {
      "id": "facebook-ads",
      "name": "Facebook Ads Daily Extraction",
      "next_run": "2026-02-21T06:00:00-03:00",
      "last_run": "2026-02-20T06:00:15-03:00",
      "last_status": "SUCCESS",
      "last_duration_seconds": 45
    },
    ...
  ]
}
```

### GET /api/jobs/{id}/logs
**Response:**
```json
{
  "job_id": "hotmart",
  "logs": [
    {
      "timestamp": "2026-02-20T06:15:23-03:00",
      "status": "SUCCESS",
      "duration": 32,
      "output": "✅ 45 vendas extraídas",
      "errors": null
    },
    {
      "timestamp": "2026-02-19T06:15:40-03:00",
      "status": "SUCCESS",
      "duration": 28,
      "output": "✅ 52 vendas extraídas",
      "errors": null
    }
  ]
}
```

### POST /api/jobs/{id}/execute
**Request:** `POST /api/jobs/hotmart/execute`
**Response:**
```json
{
  "id": "hotmart",
  "status": "RUNNING",
  "message": "Job dispatched"
}
```

### GET /health
**Response:**
```json
{
  "status": "ok",
  "scheduler": "running",
  "jobs_scheduled": 4
}
```

---

## 🖥️ Frontend - Dashboard UX

**Layout simples:**

```
┌─────────────────────────────────────────┐
│  Huli Automations Hub - Mission Control │
│  Last Updated: 2026-02-20 14:32:45     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ JOBS STATUS                             │
├─────────────────────────────────────────┤
│                                         │
│ 📱 Facebook Ads Daily Extraction        │
│    Next: 2026-02-21 06:00 (17h 28m)    │
│    Last: ✅ SUCCESS (45s) 2026-02-20   │
│    [Execute Now]                        │
│                                         │
│ 💰 Hotmart Daily Sales                  │
│    Next: 2026-02-21 06:15 (17h 43m)    │
│    Last: ✅ SUCCESS (32s) 2026-02-20   │
│    [Execute Now]                        │
│                                         │
│ 🔗 HULI Consolidator                    │
│    Next: 2026-02-21 06:45 (18h 13m)    │
│    Last: ✅ SUCCESS (28s) 2026-02-20   │
│    [Execute Now]                        │
│                                         │
│ 📊 Análise Semanal de Funis             │
│    Next: 2026-02-26 07:00 (5d 17h)     │
│    Last: ✅ SUCCESS (2m 15s) 2026-02-19│
│    [Execute Now]                        │
│                                         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ RECENT LOGS - Hotmart                   │
├─────────────────────────────────────────┤
│ 2026-02-20 06:15:23 ✅ SUCCESS (32s)    │
│ 2026-02-19 06:15:40 ✅ SUCCESS (28s)    │
│ 2026-02-18 06:15:15 ✅ SUCCESS (35s)    │
│ 2026-02-17 06:15:22 ❌ ERROR (timeout)  │
│   Error: Script timeout after 180s      │
└─────────────────────────────────────────┘
```

**Funcionalidades:**
- Auto-refresh a cada 30s
- Click "Execute Now" → job roda imediatamente
- Click em job → mostra últimos 10 logs
- Status visual (✅/❌)
- Countdown para próxima execução

---

## 🔑 Pontos Críticos

### 1. Timezone (CRÍTICO!)
```python
from pytz import timezone
tz = timezone('America/Sao_Paulo')

# Todos os horários devem usar esse timezone
scheduler.add_job(..., timezone=tz)
```

### 2. Subprocess Execution
```python
# Use subprocess.run() com capture_output=True
result = subprocess.run(
    ['python3', script_path],
    capture_output=True,
    text=True,
    timeout=job_timeout,
    cwd=os.path.dirname(script_path)
)
```

### 3. Logging JSON Estruturado
```python
log_entry = {
    "timestamp": datetime.now(tz).isoformat(),
    "status": "SUCCESS" or "ERROR",
    "duration": seconds,
    "output": stdout,
    "errors": stderr or None
}
```

### 4. Script Paths
- Scripts estão em: `/Users/matheusribeiro/Desktop/brain/automations/`
- Você pode copiar para `./jobs/` ou apontar para lá
- Certifique-se de manter credenciais em `.env`

### 5. Credenciais
```bash
# .env deve ter:
HOTMART_CLIENT_ID=...
HOTMART_CLIENT_SECRET=...
HOTMART_BASIC_TOKEN=...
FACEBOOK_ACCESS_TOKEN=...
FACEBOOK_SHEET_ID=...
# etc
```

---

## ✅ Definition of Done - MVP

Quando isso estiver pronto:

- [ ] FastAPI server rodando em localhost:8000
- [ ] /api/jobs retorna lista de 4 jobs
- [ ] APScheduler agendando corretamente
- [ ] Jobs executando nos horários certos
- [ ] Logs salvos em JSON estruturado
- [ ] Dashboard mostrando status ao vivo
- [ ] "Execute Now" funcionando para cada job
- [ ] Auto-refresh a cada 30s
- [ ] Tratamento robusto de erros
- [ ] README com instruções de setup

---

## 🚀 Como Começar

1. **Clone/setup repo:**
   ```bash
   cd /Users/matheusribeiro/Desktop/HULI-VELL
   python -m venv venv
   source venv/bin/activate
   pip install fastapi uvicorn apscheduler python-dotenv requests
   ```

2. **Estruture o código** conforme árvore acima

3. **Copie scripts:**
   ```bash
   cp -r /Users/matheusribeiro/Desktop/brain/automations/*.py ./jobs/
   ```

4. **Crie .env:**
   ```bash
   # Copy de ~/.openclaw/secrets/chaves_de_acesso.env
   cp ~/.openclaw/secrets/chaves_de_acesso.env .env
   ```

5. **Teste localmente:**
   ```bash
   python main.py
   # Acesse http://localhost:8000
   ```

---

## ❓ Dúvidas?

Contexto completo está em:
- `/docs/prd.md` - Product Requirements Document
- `/docs/DEV_BRIEFING.md` - Este arquivo
- `/Users/matheusribeiro/Desktop/brain/automations/` - Scripts originais

---

**Ready to code! 🚀**

*Briefing criado por Morgan (PM) - 2026-02-20*

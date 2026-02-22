# ARQUITETURA FASE 2: Mission Control Completo

**Data:** 2026-02-21
**Status:** Ready for Implementation
**Responsável:** @architect (Aria)

---

## 📊 Contexto & Requisitos

### Escala Estimada
- **Jobs:** 4 (atual) → +60 (futuro)
- **Facebook Ads:** ~3.500 linhas/mês × 19 colunas = 66.500 células/mês
- **Hotmart:** ~1.240 linhas/mês × 17 colunas = 21.080 células/mês
- **Histórico:** 10 ANOS (full retention)
- **Usuários simultâneos:** Máximo 3
- **SLA Dashboard:** 7 segundos para carregar gráficos

### Requisitos Não-Funcionais (NFRs)
- ✅ Performance: Gráficos carregam em < 7 seg
- ✅ Durabilidade: 10 anos de dados sem perda
- ✅ Escalabilidade: Suportar +60 jobs
- ✅ Monitoramento: Health check de APIs
- ✅ Disponibilidade: Supabase manages 99.9% uptime

---

## 🏗️ Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                             │
│  (Dashboard HTML/CSS/JS + Chart.js)                         │
│  - Gráficos de execução (sucesso/erro %)                    │
│  - Histórico últimos 30 dias                                │
│  - Skills & Health Status                                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       FASTAPI BACKEND                         │
│  - /api/executions/history (com agregação)                  │
│  - /api/skills/health                                       │
│  - Supabase client (connection pool)                        │
│  - Scheduled health checks (async tasks)                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    SUPABASE POSTGRESQL                        │
│  - job_executions (histórico 10 anos)                       │
│  - facebook_ads_data (histórico completo)                   │
│  - hotmart_data (histórico completo)                        │
│  - api_health_checks (logs de health)                       │
│  - Indices & Partitioning por ANO                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 SCHEMA PostgreSQL (Supabase)

### 1. Tabela: `job_executions` (PRINCIPAL)

```sql
CREATE TABLE job_executions (
  -- PK & Identification
  id BIGSERIAL PRIMARY KEY,
  job_id VARCHAR(64) NOT NULL,
  job_name VARCHAR(255) NOT NULL,

  -- Execution Details
  status VARCHAR(20) NOT NULL, -- SUCCESS, ERROR, RUNNING, TIMEOUT
  duration_seconds FLOAT,
  output TEXT,
  errors TEXT,

  -- Timestamps (CRITICAL for performance)
  executed_at TIMESTAMP WITH TIME ZONE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Execution context
  retry_count INT DEFAULT 0,
  timeout_seconds INT,
  exit_code INT
) PARTITION BY RANGE (EXTRACT(YEAR FROM executed_at));

-- PARTITIONS (10 anos: 2016-2026)
CREATE TABLE job_executions_2016 PARTITION OF job_executions
  FOR VALUES FROM (2016) TO (2017);
CREATE TABLE job_executions_2017 PARTITION OF job_executions
  FOR VALUES FROM (2017) TO (2018);
-- ... continuar até 2026
CREATE TABLE job_executions_2026 PARTITION OF job_executions
  FOR VALUES FROM (2026) TO (2027);

-- INDICES (críticos para gráficos & queries)
CREATE INDEX idx_job_executions_job_id ON job_executions(job_id);
CREATE INDEX idx_job_executions_executed_at ON job_executions(executed_at DESC);
CREATE INDEX idx_job_executions_status ON job_executions(status);
CREATE INDEX idx_job_executions_job_status_date ON job_executions(job_id, status, executed_at DESC);
```

**Estimativa de dados:**
- 4 jobs × 2 execuções/dia = 8 linhas/dia
- Futuramente: 60 jobs × 2 execuções/dia = 120 linhas/dia
- 10 anos × 365 dias = ~292.000 linhas (atual) / ~4.380.000 (futuro)
- Tamanho: ~150 MB (atual) / ~2 GB (futuro) - manageable

---

### 2. Tabela: `facebook_ads_data`

```sql
CREATE TABLE facebook_ads_data (
  -- PK
  id BIGSERIAL PRIMARY KEY,

  -- Campaign/Ad Info
  campaign_id VARCHAR(64) NOT NULL,
  campaign_name VARCHAR(255),
  ad_id VARCHAR(64),
  ad_name VARCHAR(255),
  account_id VARCHAR(64) NOT NULL,

  -- Metrics (19 colunas esperadas)
  spend DECIMAL(10, 2),
  impressions BIGINT,
  reach BIGINT,
  clicks BIGINT,
  conversions BIGINT,
  ctr DECIMAL(5, 2), -- Click-through rate
  cpc DECIMAL(8, 2), -- Cost per click
  cpm DECIMAL(8, 2), -- Cost per thousand
  roas DECIMAL(5, 2), -- Return on ad spend
  conversion_rate DECIMAL(5, 2),
  cost_per_conversion DECIMAL(8, 2),
  messages BIGINT,
  leads BIGINT,
  video_views BIGINT,
  frequency DECIMAL(5, 2),

  -- Custom metrics
  custom_metric_1 DECIMAL(10, 2),
  custom_metric_2 DECIMAL(10, 2),

  -- Timestamps
  date DATE NOT NULL,
  synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Data provenance
  source_job_id VARCHAR(64)
) PARTITION BY RANGE (EXTRACT(YEAR FROM date));

-- PARTITIONS (10 anos)
CREATE TABLE facebook_ads_data_2016 PARTITION OF facebook_ads_data
  FOR VALUES FROM (2016) TO (2017);
-- ... continuar até 2026

-- INDICES
CREATE INDEX idx_facebook_ads_data_account_date ON facebook_ads_data(account_id, date DESC);
CREATE INDEX idx_facebook_ads_data_campaign_date ON facebook_ads_data(campaign_id, date DESC);
CREATE INDEX idx_facebook_ads_data_date ON facebook_ads_data(date DESC);
```

**Estimativa de dados:**
- 3.500 linhas/mês × 12 meses × 10 anos = 420.000 linhas
- Tamanho: ~200 MB - manageable

---

### 3. Tabela: `hotmart_data`

```sql
CREATE TABLE hotmart_data (
  -- PK
  id BIGSERIAL PRIMARY KEY,

  -- Transaction Info
  transaction_id VARCHAR(64) UNIQUE NOT NULL,
  transaction_status VARCHAR(20), -- paid, pending, refunded

  -- Product Info
  product_id VARCHAR(64),
  product_name VARCHAR(255),
  producer_id VARCHAR(64),

  -- Sales Details (17 colunas esperadas)
  buyer_name VARCHAR(255),
  buyer_email VARCHAR(255),
  price DECIMAL(10, 2),
  commissions DECIMAL(10, 2),
  payment_method VARCHAR(50), -- credit_card, boleto, pix
  currency VARCHAR(3) DEFAULT 'BRL',

  -- Advanced fields
  source VARCHAR(100), -- utm_source equivalent
  coupon_code VARCHAR(100),
  installments INT DEFAULT 1,
  traffic_source VARCHAR(100),

  -- Dates (CRITICAL for historical queries)
  sale_date DATE NOT NULL,
  payment_date DATE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Data provenance
  source_job_id VARCHAR(64)
) PARTITION BY RANGE (EXTRACT(YEAR FROM sale_date));

-- PARTITIONS (10 anos)
CREATE TABLE hotmart_data_2016 PARTITION OF hotmart_data
  FOR VALUES FROM (2016) TO (2017);
-- ... continuar até 2026

-- INDICES
CREATE INDEX idx_hotmart_data_sale_date ON hotmart_data(sale_date DESC);
CREATE INDEX idx_hotmart_data_producer_date ON hotmart_data(producer_id, sale_date DESC);
CREATE INDEX idx_hotmart_data_product_date ON hotmart_data(product_id, sale_date DESC);
CREATE UNIQUE INDEX idx_hotmart_data_transaction_id ON hotmart_data(transaction_id);
```

**Estimativa de dados:**
- 1.240 linhas/mês × 12 meses × 10 anos = 148.800 linhas
- Tamanho: ~80 MB - manageable

---

### 4. Tabela: `api_health_checks` (NOVO)

```sql
CREATE TABLE api_health_checks (
  -- PK
  id BIGSERIAL PRIMARY KEY,

  -- API Info
  api_name VARCHAR(64) NOT NULL, -- 'google_sheets', 'facebook_ads', 'hotmart', etc
  endpoint VARCHAR(255),

  -- Health Status
  status VARCHAR(20) NOT NULL, -- OK, TIMEOUT, ERROR, UNAVAILABLE
  response_time_ms INT,
  error_message TEXT,
  http_status_code INT,

  -- Timestamps
  checked_at TIMESTAMP WITH TIME ZONE NOT NULL,

  -- Context
  job_id VARCHAR(64),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- INDICES
CREATE INDEX idx_api_health_api_name_date ON api_health_checks(api_name, checked_at DESC);
CREATE INDEX idx_api_health_status ON api_health_checks(status);
```

**Estimativa de dados:**
- Health checks: 1x por API antes de cada job
- ~10 APIs × 4 jobs/dia = 40 checks/dia
- 10 anos × 365 dias = ~146.000 linhas
- Tamanho: ~15 MB - very small

---

### 5. Tabela: `consolidated_data` (OPCIONAL - Phase 2b)

```sql
CREATE TABLE consolidated_data (
  -- PK
  id BIGSERIAL PRIMARY KEY,

  -- Aggregation level
  date DATE NOT NULL,

  -- Hotmart Aggregates
  hotmart_total_revenue DECIMAL(12, 2),
  hotmart_transaction_count INT,
  hotmart_average_ticket DECIMAL(10, 2),

  -- Facebook Aggregates
  facebook_total_spend DECIMAL(12, 2),
  facebook_total_conversions BIGINT,
  facebook_average_cpc DECIMAL(8, 2),

  -- Combined KPIs
  roi_percentage DECIMAL(5, 2), -- (hotmart_revenue - facebook_spend) / facebook_spend
  cost_per_acquisition DECIMAL(8, 2),
  customer_lifetime_value DECIMAL(10, 2),

  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- INDICES
CREATE INDEX idx_consolidated_data_date ON consolidated_data(date DESC);
```

---

## 🚀 Performance Strategy

### 1. Query Optimization

**Para gráficos (< 7 seg):**

```sql
-- BOAS: Agregação no backend, não no frontend
SELECT
  DATE_TRUNC('day', executed_at) as execution_day,
  job_id,
  status,
  COUNT(*) as count,
  AVG(duration_seconds) as avg_duration
FROM job_executions
WHERE executed_at >= NOW() - INTERVAL '30 days'
  AND job_id = $1
GROUP BY DATE_TRUNC('day', executed_at), job_id, status
ORDER BY execution_day DESC;
```

**Índices garantem < 1 seg para 30 dias:**
- Index: `(job_id, executed_at DESC)`

### 2. Caching Strategy

**Frontend caching:**
- Cache últimos 30 dias em localStorage
- Refresh a cada 30 min ou ao clicar
- Economiza banda passante

**Backend caching:**
- Redis para resultados de agregação (opcional, Phase 2b)
- TTL: 5 minutos para dados de hoje
- TTL: permanente para dados passados

### 3. Particionamento (JÁ incluído no schema)

**Por ANO (2016-2026):**
- Queries sobre dados antigos não varrem partições recentes
- Limpeza de dados (se necessário) é por partição
- Exemplo: deletar 2016 = DROP TABLE job_executions_2016

**Benefício:**
- 10 anos de dados, mas query rápida
- Índices menores por partição

---

## 🔌 Backend Integration (FastAPI)

### 1. Supabase Client Connection

```python
# backend/services/supabase_service.py
from supabase import create_client
import os

class SupabaseService:
    def __init__(self):
        self.client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )

    def get_execution_history(self, job_id: str, days: int = 30):
        """Get aggregated execution history for dashboard"""
        return (
            self.client
            .table("job_executions")
            .select("""
                date_trunc('day', executed_at) as day,
                status,
                COUNT(*) as count,
                AVG(duration_seconds) as avg_duration
            """)
            .eq("job_id", job_id)
            .gte("executed_at", f"now()-{days} days")
            .order("day", desc=True)
            .execute()
        )

    def log_execution(self, job_id: str, result):
        """Insert execution log"""
        return (
            self.client
            .table("job_executions")
            .insert({
                "job_id": job_id,
                "job_name": result.job_name,
                "status": result.status,
                "duration_seconds": result.duration,
                "output": result.output,
                "errors": result.errors,
                "executed_at": result.timestamp,
                "exit_code": result.exit_code
            })
            .execute()
        )

    def check_api_health(self, api_name: str, status: str, response_time_ms: int, error: str = None):
        """Log API health check"""
        return (
            self.client
            .table("api_health_checks")
            .insert({
                "api_name": api_name,
                "status": status,
                "response_time_ms": response_time_ms,
                "error_message": error,
                "checked_at": "now()"
            })
            .execute()
        )
```

### 2. API Endpoints (Novos)

```python
# backend/api/analytics.py
from fastapi import APIRouter
from backend.services.supabase_service import SupabaseService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
db = SupabaseService()

@router.get("/executions/{job_id}")
async def get_job_history(job_id: str, days: int = 30):
    """Get execution history for job (aggregated by day)"""
    data = db.get_execution_history(job_id, days)
    return {
        "job_id": job_id,
        "period_days": days,
        "data": data.data
    }

@router.get("/skills/health")
async def get_api_health_status():
    """Get current health status of all APIs"""
    apis = ["google_sheets", "facebook_ads", "hotmart", "google_drive"]
    results = {}

    for api_name in apis:
        latest = (
            db.client
            .table("api_health_checks")
            .select("*")
            .eq("api_name", api_name)
            .order("checked_at", desc=True)
            .limit(1)
            .execute()
        )
        results[api_name] = latest.data[0] if latest.data else None

    return results

@router.post("/executions")
async def log_execution(job_id: str, result: dict):
    """Log execution to Supabase (called by scheduler)"""
    return db.log_execution(job_id, result)
```

### 3. Health Check Service (Async)

```python
# backend/services/health_check_service.py
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class HealthCheckService:
    def __init__(self, db_service):
        self.db = db_service
        self.scheduler = AsyncIOScheduler()

    async def check_google_sheets(self):
        """Test Google Sheets API"""
        try:
            # Attempt to list files (lightweight)
            response = google_api.list_files(limit=1)
            await self.db.check_api_health(
                "google_sheets", "OK",
                response_time_ms=int(response['response_time']*1000)
            )
        except Exception as e:
            await self.db.check_api_health(
                "google_sheets", "ERROR", 0, str(e)
            )

    async def check_facebook_ads(self):
        """Test Facebook Ads API"""
        # Similar pattern
        pass

    async def check_hotmart(self):
        """Test Hotmart API"""
        # Similar pattern
        pass

    def start(self):
        """Schedule health checks 10 min before job execution"""
        # Before 6:00 AM Hotmart job → Check at 5:50 AM
        self.scheduler.add_job(
            self.check_hotmart,
            'cron', hour=5, minute=50, timezone='America/Sao_Paulo'
        )
        # Before 6:00 AM Facebook job → Check at 5:50 AM
        self.scheduler.add_job(
            self.check_facebook_ads,
            'cron', hour=5, minute=50, timezone='America/Sao_Paulo'
        )
        # Before 6:45 AM Consolidator → Check at 6:40 AM
        self.scheduler.add_job(
            self.check_google_sheets,
            'cron', hour=6, minute=40, timezone='America/Sao_Paulo'
        )
        self.scheduler.start()
```

---

## 🎨 Frontend Integration

### 1. Dashboard Charts (Chart.js)

```html
<!-- frontend/dashboard.html - NEW -->
<div id="executionsChart"></div>
<div id="successRateChart"></div>
<div id="apiHealthChart"></div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
<script>
async function loadExecutionHistory(jobId) {
  const response = await fetch(`/api/analytics/executions/${jobId}?days=30`);
  const data = await response.json();

  // Transform data for Chart.js
  const labels = data.data.map(d => d.day);
  const successCounts = data.data.map(d => d.count);

  const ctx = document.getElementById('executionsChart').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: `${jobId} - Últimos 30 dias`,
        data: successCounts,
        borderColor: '#10b981',
        tension: 0.4
      }]
    }
  });
}

async function loadAPIHealth() {
  const response = await fetch(`/api/analytics/skills/health`);
  const data = await response.json();

  const healthDiv = document.getElementById('apiHealthChart');
  healthDiv.innerHTML = '';

  Object.entries(data).forEach(([api, status]) => {
    const statusColor = status.status === 'OK' ? '🟢' : '🔴';
    healthDiv.innerHTML += `
      <div>
        ${statusColor} ${api}: ${status.status}
        (${status.response_time_ms}ms)
      </div>
    `;
  });
}

// Load on page init
document.addEventListener('DOMContentLoaded', () => {
  loadExecutionHistory('facebook-ads');
  loadAPIHealth();
  setInterval(loadAPIHealth, 300000); // Refresh every 5 min
});
</script>
```

### 2. Skills Section (HTML)

```html
<!-- frontend/skills.html -->
<section id="skills" class="skills-section">
  <h2>🛠️ Ferramentas & Status de Conexão</h2>

  <div class="skills-grid">
    <div class="skill-card">
      <h3>📊 Google Sheets</h3>
      <div id="google-status" class="status">Checking...</div>
      <div id="google-time" class="response-time"></div>
    </div>

    <div class="skill-card">
      <h3>📱 Facebook Ads</h3>
      <div id="facebook-status" class="status">Checking...</div>
      <div id="facebook-time" class="response-time"></div>
    </div>

    <div class="skill-card">
      <h3>💰 Hotmart</h3>
      <div id="hotmart-status" class="status">Checking...</div>
      <div id="hotmart-time" class="response-time"></div>
    </div>

    <div class="skill-card">
      <h3>☁️ Google Drive</h3>
      <div id="drive-status" class="status">Checking...</div>
      <div id="drive-time" class="response-time"></div>
    </div>
  </div>
</section>
```

---

## 🔄 Deployment Strategy

### Supabase Setup (5 min)
1. Criar account em supabase.com
2. Criar novo project
3. Rodar migrations (SQL scripts acima)
4. Copiar SUPABASE_URL e SUPABASE_KEY para .env

### Backend Changes (1-2 horas)
1. Adicionar `supabase-py` ao requirements.txt
2. Criar `SupabaseService`
3. Integrar em job_scheduler (log executions)
4. Adicionar endpoints `/api/analytics`
5. Implementar `HealthCheckService`

### Frontend Changes (1-2 horas)
1. Adicionar Chart.js
2. Criar gráficos de histórico
3. Criar seção de skills & health
4. Integrar no dashboard existente

### Testing (1 hora)
1. Verificar carregamento de gráficos (< 7 seg)
2. Testar health checks
3. Validar histórico (insira alguns dados de teste)

---

## 📋 Estimativa de Esforço

| Componente | Horas | Responsável |
|-----------|-------|-------------|
| Schema design & migrations | 1 | @architect |
| Supabase setup | 0.5 | @data-engineer |
| Backend integration | 2 | @dev |
| Frontend charts | 1.5 | @dev |
| Health check service | 1 | @dev |
| Testing & deployment | 1 | @dev |
| **TOTAL** | **~7 horas** | — |

---

## 🎯 Success Criteria

- ✅ Gráficos carregam em < 7 segundos
- ✅ 10 anos de histórico armazenados
- ✅ API health status atualiza a cada 5 minutos
- ✅ Dashboard mostra últimos 30 dias com clareza
- ✅ Skills section mostra status de todas as APIs
- ✅ Zero data loss em transição JSON → PostgreSQL

---

## 📝 Próximos Passos

1. **@data-engineer (Dara):** Review schema, sugerir índices adicionais, preparar migrations SQL
2. **@dev (Dex):** Implementar backend + frontend conforme arquitetura acima
3. **Testing:** Validar performance com dados reais

---

*Arquitetura desenhada por Aria (Architect) - 2026-02-21*

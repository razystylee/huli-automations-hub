# Testing & Validation Guide
## Huli-VELLHUB - Todas as Fases

**Data:** 2026-02-21
**Objetivo:** Validar integração completa Fase 1-5

---

## 🧪 Testes por Fase

### FASE 1: Supabase PostgreSQL Setup

#### Teste 1.1: Verificar Supabase Conexão
```bash
# No Supabase Console (https://app.supabase.com)
# 1. Login com suas credenciais
# 2. Selecione projeto: cgikjrpmchycolppzcvy
# 3. Vá para SQL Editor
# 4. Execute:
SELECT count(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';
# Esperado: 4 tabelas (facebook_ads_data, hotmart_data, job_executions, api_health_checks)
```

#### Teste 1.2: Verificar Partições
```sql
-- No SQL Editor, execute:
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public' AND tablename LIKE 'facebook_ads_data%'
ORDER BY tablename;

-- Esperado: facebook_ads_data_2024, facebook_ads_data_2023, ..., facebook_ads_data_2016
-- Total: 11 partições
```

#### Teste 1.3: Verificar RLS
```sql
-- No SQL Editor, execute:
SELECT tablename, rowsecurity FROM pg_tables
WHERE schemaname = 'public';

-- Esperado: rowsecurity = true para todas as tabelas
```

**Status:** ✅ PASS se todos os testes executam

---

### FASE 2: CSV Data Loading

#### Teste 2.1: Verificar Contagem de Dados
```sql
-- No SQL Editor, execute:
SELECT
    'facebook_ads_data' as table_name, count(*) as row_count FROM facebook_ads_data
UNION ALL
SELECT
    'hotmart_data', count(*) FROM hotmart_data;

-- Esperado:
-- facebook_ads_data: 2855 rows
-- hotmart_data: 433 rows
-- Total: 3288 rows
```

#### Teste 2.2: Verificar Datas
```sql
-- No SQL Editor, execute:
SELECT
    min(date) as min_date,
    max(date) as max_date,
    count(*) as total_rows
FROM facebook_ads_data;

-- Esperado:
-- min_date: 2020-01-01 (ou próximo à 2020)
-- max_date: 2024-12-31 (ou próximo à 2024)
```

#### Teste 2.3: Verificar Integridade de Dados
```sql
-- No SQL Editor, execute:
SELECT
    count(*) as total,
    count(DISTINCT transaction_id) as unique_transactions,
    count(DISTINCT date) as unique_dates
FROM facebook_ads_data;

-- Esperado: total = unique_transactions (sem duplicatas)
```

**Status:** ✅ PASS se contagens coincidem (2855 + 433)

---

### FASE 3: RLS & Security Setup

#### Teste 3.1: Verificar RLS Policies
```sql
-- No SQL Editor, execute:
SELECT schemaname, tablename, policyname
FROM pg_policies
WHERE schemaname = 'public';

-- Esperado: Mostrar estrutura de policies (mesmo que vazias/não ativas)
```

#### Teste 3.2: Verificar Credenciais
```bash
# Na raiz do projeto, verifique .env:
cat .env | grep SUPABASE

# Esperado:
# SUPABASE_URL=https://cgikjrpmchycolppzcvy.supabase.co
# SUPABASE_ANON_KEY=...
# SUPABASE_SERVICE_ROLE_KEY=...
```

**Status:** ✅ PASS se RLS habilitado e credenciais configuradas

---

### FASE 4: Backend FastAPI Integration

#### Teste 4.1: Iniciar Backend
```bash
cd /Users/matheusribeiro/Desktop/HULI-VELL/backend
python main.py

# Esperado no console:
# INFO:     Started server process [PID]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Teste 4.2: Testar Endpoint Health
```bash
curl -s http://localhost:8000/api/health | python -m json.tool

# Esperado:
{
  "status": "ok",
  "app": "Huli-VELLHUB",
  "version": "1.0.0",
  "scheduler": "running",
  "jobs_count": N
}
```

#### Teste 4.3: Testar Endpoint Analytics
```bash
curl -s "http://localhost:8000/api/analytics/skills/health" | python -m json.tool

# Esperado:
{
  "skills": {
    "api_name": {
      "status": "UP",
      "response_time_ms": 123,
      "error": "",
      "last_checked": "2026-02-21T...",
      "http_status": 200
    }
  },
  "total_apis": N,
  "healthy_count": N,
  "timestamp": "2026-02-21T..."
}
```

#### Teste 4.4: Executar Testes de Integração
```bash
cd /Users/matheusribeiro/Desktop/HULI-VELL/backend
python test_supabase_integration.py

# Esperado:
# ✅ PASS: Credentials
# ✅ PASS: Client Initialization
# ✅ PASS: Database Access
# ✅ PASS: Log Execution
# ✅ PASS: Get Statistics
# ✅ PASS: API Health Logging
# Results: 6/6 tests passed
```

**Status:** ✅ PASS se todos endpoints respondem e testes passam

---

### FASE 5: Frontend Chart.js Integration

#### Teste 5.1: Verificar Arquivos Frontend
```bash
# Verificar que Chart.js foi adicionado
grep -n "chart.js" /Users/matheusribeiro/Desktop/HULI-VELL/frontend/index.html

# Esperado:
# 9:<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
```

#### Teste 5.2: Verificar Funções JavaScript
```bash
# Verificar que funções de analytics foram adicionadas
grep -n "function fetchAnalyticsData" /Users/matheusribeiro/Desktop/HULI-VELL/frontend/app.js
grep -n "function renderAnalytics" /Users/matheusribeiro/Desktop/HULI-VELL/frontend/app.js
grep -n "function renderHealthStatus" /Users/matheusribeiro/Desktop/HULI-VELL/frontend/app.js

# Esperado: 3 matches encontradas
```

#### Teste 5.3: Verificar CSS para Analytics
```bash
# Verificar que estilos analytics foram adicionados
grep -n ".analytics-section" /Users/matheusribeiro/Desktop/HULI-VELL/frontend/style.css
grep -n ".health-card" /Users/matheusribeiro/Desktop/HULI-VELL/frontend/style.css
grep -n ".chart-container" /Users/matheusribeiro/Desktop/HULI-VELL/frontend/style.css

# Esperado: 3 matches encontradas
```

#### Teste 5.4: Acessar Frontend no Browser
```
1. Abra http://localhost:8000 no navegador
2. Verifique que carrega sem erros de console
3. Aguarde 30 segundos para primeiro refresh

4. Observar:
   ✅ Jobs Grid: Mostrando status de jobs
   ✅ Logs Table: Mostrando histórico de execuções
   ✅ Analytics Section: Gráfico de execuções + health cards
   ✅ Chart.js: Gráfico está renderizado
   ✅ Health Cards: Status UP/DOWN/DEGRADED

5. Abra DevTools (F12) → Console
   ✅ Sem erros de JavaScript
   ✅ Analytics refresh logs aparecem a cada 5 minutos
```

#### Teste 5.5: Validar Performance
```javascript
// No console do browser, execute:
performance.getEntriesByType('navigation')[0];

// Observar:
// loadEventEnd - loadEventStart < 5000 (< 5s)

// Ou para teste mais detalhado:
const entries = performance.getEntriesByType('resource');
console.log('Total resources:', entries.length);
console.log('Total load time:', Math.max(...entries.map(e => e.responseEnd)));
// Esperado: < 7000ms (< 7s)
```

**Status:** ✅ PASS se todos elementos aparecem e sem erros

---

## 🔄 Teste de Integração Completa

### Setup
```bash
# Terminal 1: Iniciar Backend
cd /Users/matheusribeiro/Desktop/HULI-VELL/backend
python main.py

# Terminal 2: Abrir Browser
open http://localhost:8000
# ou: curl http://localhost:8000
```

### Cenário de Teste
```
1. [T0] Página carrega - Analytics em branco (sem dados ainda)
2. [T0] Aguardar 30 segundos - Job status atualiza
3. [T0+5min] Analytics atualizam - Gráfico renderiza dados
4. [T0+10min] Health cards atualizam - Status das APIs
5. [Verificação] Clicar em "Execute Now" para um job
   - Backend executa o job
   - Logs Table atualiza em 30 segundos
   - Após 5 minutos, Analytics refletem nova execução
```

### Métricas a Acompanhar
```
- ✅ Frontend carrega em < 3s
- ✅ API responses < 2s
- ✅ Chart.js renderiza em < 2s
- ✅ Auto-refresh job status cada 30s
- ✅ Auto-refresh analytics cada 5min
- ✅ Browser DevTools Console: sem erros
- ✅ Network tab: todos requests 200 OK
- ✅ Performance: Lighthouse score > 80
```

---

## 🐛 Troubleshooting

### Problema: "Supabase service not configured"
```
Solução:
1. Verificar .env tem SUPABASE_URL e SUPABASE_ANON_KEY
2. Verificar que credentials são válidas em https://app.supabase.com
3. Teste comando: curl https://cgikjrpmchycolppzcvy.supabase.co/auth/v1/
```

### Problema: "Cannot GET /api/analytics/executions"
```
Solução:
1. Verificar que backend está rodando em http://localhost:8000
2. Verificar que job_executions table tem dados
3. Checar logs do backend para erros
```

### Problema: "Chart.js is not defined"
```
Solução:
1. Verificar que Chart.js CDN está sendo carregado (DevTools → Network)
2. Verificar que script tag está antes de app.js no HTML
3. Se offline, baixar Chart.js localmente: https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js
```

### Problema: "Analytics section doesn't render"
```
Solução:
1. Verificar que frontend/app.js tem funções renderAnalytics()
2. Verificar que HTML tem divs com IDs: executionChart, apiHealthStatus
3. Abrir DevTools Console e executar:
   console.log(state.analyticsData);
   console.log(state.healthData);
   // Verificar que não são null
```

### Problema: "RLS policy blocking inserts"
```
Solução:
1. Verificar que backend usa SERVICE_ROLE_KEY para writes
2. Na Supabase Console, temporariamente desabilitar RLS:
   ALTER TABLE job_executions DISABLE ROW LEVEL SECURITY;
3. Para re-habilitar:
   ALTER TABLE job_executions ENABLE ROW LEVEL SECURITY;
```

---

## ✅ Checklist Final

### Antes de Produção

```
FASE 1: Database
- [ ] Supabase project criado
- [ ] 4 tabelas criadas
- [ ] 11 partições funcionando
- [ ] RLS habilitado
- [ ] Índices criados
- [ ] Credentials em .env

FASE 2: Data Loading
- [ ] CSV files disponíveis
- [ ] 2,855 facebook_ads registros carregados
- [ ] 433 hotmart registros carregados
- [ ] Sem duplicatas
- [ ] Datas validadas (2020-2024)

FASE 3: Security
- [ ] RLS policies template definido
- [ ] SERVICE_ROLE_KEY configurado
- [ ] ANON_KEY configurado
- [ ] Nenhuma credencial hardcoded

FASE 4: Backend
- [ ] FastAPI rodando sem erros
- [ ] /api/health responde 200
- [ ] /api/analytics/* endpoints respondendo
- [ ] 6/6 testes de integração PASSED
- [ ] Supabase service inicializado
- [ ] Logging funcionando

FASE 5: Frontend
- [ ] index.html carrega sem erros
- [ ] Chart.js importado via CDN
- [ ] app.js funções de analytics presentes
- [ ] style.css analytics styles presentes
- [ ] Analytics section renderiza
- [ ] Chart renderiza dados
- [ ] Health cards aparecem
- [ ] Auto-refresh 30s para jobs
- [ ] Auto-refresh 5min para analytics
- [ ] Responsive em mobile/tablet/desktop
- [ ] Performance < 7s SLA

VALIDAÇÃO CROSS-STACK
- [ ] Backend → Supabase connection OK
- [ ] Frontend → Backend API calls OK
- [ ] Data flow: CSV → DB → API → Chart
- [ ] DevTools Console: sem erros
- [ ] Lighthouse score > 80
```

---

## 📊 Métricas Esperadas

### Database
- **Queries:** < 500ms
- **Partitions:** 11 (2016-2026)
- **Data rows:** 3,288
- **Table size:** < 50MB

### Backend
- **Startup time:** < 5s
- **API response:** < 1s
- **Supabase fetch:** < 2s
- **Error rate:** 0%

### Frontend
- **Page load:** < 3s
- **Chart render:** < 2s
- **API fetch:** < 2s
- **Total dashboard:** < 5s
- **Lighthouse score:** > 80
- **Mobile score:** > 70

---

## 📝 Test Report Template

```markdown
# Huli-VELLHUB - Test Report
**Date:** 2026-02-21
**Tester:** [name]

## Summary
- Fases Testadas: 1, 2, 3, 4, 5
- Total Testes: XX
- Passed: XX ✅
- Failed: 0
- Blocked: 0

## Phase Results
### Fase 1: Database
- [ ] PASS
- Notes:

### Fase 2: Data Loading
- [ ] PASS
- Notes:

### Fase 3: Security
- [ ] PASS
- Notes:

### Fase 4: Backend
- [ ] PASS
- Notes:

### Fase 5: Frontend
- [ ] PASS
- Notes:

## Performance Metrics
- Frontend load: ___ ms
- API response: ___ ms
- Chart render: ___ ms
- SLA compliance: ___ %

## Issues Found
1. [Issue 1]
2. [Issue 2]

## Conclusion
Ready for production: YES / NO

Signed: [name] - [date]
```

---

## 🚀 Conclusão

Todos os testes devem PASS ✅ antes de publicar em produção.

Se algum teste falhar, verifique a seção **Troubleshooting** acima.

**Status:** Pronto para validação completa! 🎉

---

**Huli-VELLHUB v1.0.0 - Testing & Validation Guide**
**Data:** 2026-02-21

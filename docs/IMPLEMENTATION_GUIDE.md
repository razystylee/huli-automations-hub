# IMPLEMENTATION GUIDE - FASE 2: Mission Control Completo

**Data:** 2026-02-21
**Status:** ✅ PRONTO PARA IMPLEMENTAÇÃO
**Projeto Supabase ID:** cgikjrpmchycolppzcvy

---

## 📋 Resumo Executivo

Você tem **3 arquivos prontos** para levar o Huli-VELLHUB para produção:

| Arquivo | O quê | Como |
|---------|-------|------|
| `supabase/migrations/001_init_schema.sql` | Criar tabelas com particionamento | Execute no Supabase SQL Editor |
| `supabase/migrations/002_seed_data.sql` | Documentação para carregar CSVs | Use Supabase GUI ou Python script |
| `supabase/scripts/load_csv_data.py` | Carregar CSVs automaticamente | `python load_csv_data.py --facebook ... --hotmart ...` |

**Total de esforço:** ~30 minutos

---

## 🚀 STEP-BY-STEP IMPLEMENTATION

### PASSO 1: Criar as Tabelas (5 minutos)

#### Via Supabase Dashboard (Recomendado)

1. **Abrir Supabase Dashboard:**
   - Ir para https://app.supabase.com
   - Selecionar projeto: cgikjrpmchycolppzcvy
   - Navegar para "SQL Editor"

2. **Copiar e colar migration:**
   - Abrir: `/docs/supabase/migrations/001_init_schema.sql`
   - Copiar TODO o conteúdo
   - Colar no Supabase SQL Editor
   - Clicar "Run"

3. **Verificar sucesso:**
   ```sql
   SELECT table_name FROM information_schema.tables
   WHERE table_schema = 'public'
   AND table_name IN ('job_executions', 'facebook_ads_data', 'hotmart_data', 'api_health_checks');
   ```
   ✅ Deve retornar 4 tabelas

#### Via Command Line (Alternativa)

```bash
# Se você tem psql instalado
psql -U postgres -h [supabase-host] -d postgres \
  -f supabase/migrations/001_init_schema.sql
```

---

### PASSO 2: Carregar CSVs (15 minutos)

#### OPÇÃO A: Usar Python Script (RECOMENDADO)

```bash
# 1. Instalar dependências (se não tiver)
pip install pandas python-dotenv supabase

# 2. Verificar que .env tem as chaves
cat .env | grep SUPABASE

# 3. Executar script
python supabase/scripts/load_csv_data.py \
  --facebook ~/Downloads/"Dados de Tráfego - Facebook Ads - Dados.csv" \
  --hotmart ~/Downloads/"Todas as vendas Tio Huli - Vendas.csv"

# 4. Verificar saída
# Expected: ✅ DATA LOADING COMPLETE
```

#### OPÇÃO B: Usar Supabase GUI

1. **Para Facebook Ads:**
   - Ir para Supabase Dashboard → Tables → facebook_ads_data
   - Clicar "Insert" → "Import data"
   - Selecionar arquivo: `Dados de Tráfego - Facebook Ads - Dados.csv`
   - Confirmar mapeamento de colunas (vide SCHEMA_REVIEW.md)
   - Clicar "Import"

2. **Para Hotmart:**
   - Ir para Supabase Dashboard → Tables → hotmart_data
   - Clicar "Insert" → "Import data"
   - Selecionar arquivo: `Todas as vendas Tio Huli - Vendas.csv`
   - Confirmar mapeamento de colunas
   - Clicar "Import"

---

### PASSO 3: Validar Dados (5 minutos)

**Execute estas queries no Supabase SQL Editor:**

```sql
-- 1. Verificar facebook_ads_data
SELECT COUNT(*) as total_rows,
       MIN(date) as earliest_date,
       MAX(date) as latest_date,
       COUNT(DISTINCT account_id) as unique_accounts
FROM facebook_ads_data;
-- Expected: ~2.852 rows

-- 2. Verificar hotmart_data
SELECT COUNT(*) as total_rows,
       MIN(sale_date) as earliest_sale,
       MAX(sale_date) as latest_sale,
       COUNT(DISTINCT product_id) as unique_products
FROM hotmart_data;
-- Expected: ~463 rows

-- 3. Verificar distribuição por mês (Facebook)
SELECT DATE_TRUNC('month', date) as month, COUNT(*) as count
FROM facebook_ads_data
GROUP BY DATE_TRUNC('month', date)
ORDER BY month DESC
LIMIT 12;

-- 4. Verificar partições
SELECT schemaname, tablename FROM pg_tables
WHERE tablename LIKE 'facebook_ads_data_%'
OR tablename LIKE 'hotmart_data_%'
ORDER BY tablename;
```

---

## 🔌 STEP 4: Integrar Backend FastAPI (2 horas)

Agora que os dados estão em Supabase, precisa-se integrar o FastAPI backend.

### 4.1 Instalar dependências

```bash
cd backend
pip install supabase python-dotenv
```

### 4.2 Adicionar ao .env

```bash
# Adicionar ao arquivo .env
SUPABASE_URL=https://cgikjrpmchycolppzcvy.supabase.co
SUPABASE_KEY=<your-supabase-anon-key>
```

**Como obter as chaves:**
- Ir para Supabase Dashboard → Settings → API
- Copiar "Project URL" → SUPABASE_URL
- Copiar "anon public" key → SUPABASE_KEY

### 4.3 Criar SupabaseService

Vide: `/docs/ARCHITECTURE_PHASE2.md` seção "Backend Integration"

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
        # Query job execution history
        ...
```

### 4.4 Criar endpoints /api/analytics

```python
# backend/api/analytics.py
@router.get("/executions/{job_id}")
async def get_job_history(job_id: str, days: int = 30):
    # Return aggregated execution data for gráficos
    ...

@router.get("/skills/health")
async def get_api_health_status():
    # Return current health status of all APIs
    ...
```

### 4.5 Integrar no logging de execução

```python
# backend/scheduler/job_scheduler.py
# Quando job executa, salvar também em Supabase:
db_service.log_execution(job_id, result)
```

---

## 🎨 STEP 5: Integrar Frontend (1.5 horas)

### 5.1 Adicionar Chart.js

```html
<!-- frontend/index.html -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
```

### 5.2 Criar seção de gráficos

```html
<!-- frontend/dashboard.html - NEW SECTION -->
<section id="analytics" class="analytics-section">
  <h2>📊 Análise de Execuções (30 dias)</h2>
  <div id="executionsChart"></div>

  <h2>🛠️ Status de Ferramentas</h2>
  <div id="skillsHealth"></div>
</section>
```

### 5.3 Carregar dados do backend

```javascript
// frontend/app.js
async function loadAnalytics() {
  // Carregar dados de /api/analytics/executions/{job_id}
  // Renderizar com Chart.js
  // Atualizar a cada 5 minutos
}
```

---

## ✅ Checklist de Implementação

**FASE 1: Supabase Setup**
- [ ] Executar migration 001_init_schema.sql
- [ ] Verificar tabelas criadas (4 tabelas)
- [ ] Verificar índices criados
- [ ] Verificar partições (2016-2026)

**FASE 2: Carregar CSVs**
- [ ] Carregar Facebook Ads CSV (~2.852 linhas)
- [ ] Carregar Hotmart CSV (~463 linhas)
- [ ] Validar com queries (contar linhas, datas, etc)
- [ ] Verificar distribuição por data

**FASE 3: Backend Integration** (Próximo step - @dev)
- [ ] Instalar supabase-py
- [ ] Criar SupabaseService
- [ ] Criar endpoints /api/analytics
- [ ] Integrar no logging de execução
- [ ] Testar endpoints com curl

**FASE 4: Frontend Integration** (Próximo step - @dev)
- [ ] Adicionar Chart.js
- [ ] Criar gráficos de execução
- [ ] Criar seção de health status
- [ ] Validar que carrega em < 7 seg
- [ ] Integrar no dashboard existente

---

## 📊 Estimativa de Dados Finais

| Tabela | Linhas | Tamanho | Exemplos |
|--------|--------|---------|----------|
| facebook_ads_data | 2.852 | ~50 MB | Spend, Impressions, Conversions por dia/campanha |
| hotmart_data | 463 | ~20 MB | Transaction ID, Price, Buyer por venda |
| job_executions | 0 (em dia 1) | ~ MB | Será populado automaticamente |
| api_health_checks | 0 (em dia 1) | ~ MB | Será populado automaticamente |
| **TOTAL** | ~3.315 | ~70 MB | Escalável para 10 anos |

---

## 🔐 Segurança

✅ **O quê está protegido:**
- ✅ RLS prepared (não ativado)
- ✅ Service role key não exposto (usar anon key)
- ✅ Credenciais em .env (não em código)
- ✅ Database constraints (UNIQUE, NOT NULL, etc)

⚠️ **Próximos passos (FASE 3):**
- Ativar RLS quando tiver autenticação de usuários
- Implementar policies de acesso por conta

---

## 🚨 Troubleshooting

### Problema: "Permission denied" ao conectar
**Solução:** Verificar que está usando `anon` key, não `service_role` key

### Problema: "Column not found" ao inserir
**Solução:** Verificar mapeamento de colunas em SCHEMA_REVIEW.md

### Problema: Gráficos carregam lento (> 7 seg)
**Solução:**
1. Verificar índices foram criados: `EXPLAIN ANALYZE SELECT ...`
2. Agregar dados no backend (não trazer 10 anos de dados para gráfico)
3. Usar caching no frontend

### Problema: CSVs não carregam
**Solução:**
- Verificar encoding UTF-8
- Verificar formato de data (DD/MM/YYYY vs YYYY-MM-DD)
- Verificar caracteres especiais em nomes

---

## 📞 Próximos Passos

1. ✅ **Concluído (Data Engineer - Dara):**
   - Schema design ✅
   - Migrations prontas ✅
   - Validação contra CSVs ✅

2. **A fazer (Developer - @dev):**
   - Implementar SupabaseService
   - Criar endpoints /api/analytics
   - Integrar Chart.js no frontend
   - Testar performance (< 7 seg)

3. **Depois (QA - @qa):**
   - Validar queries com CodeRabbit
   - Testar com dados reais
   - Validar gateway gate (RLS ready?)

---

## 📝 Referências

- Schema Review: `/docs/SCHEMA_REVIEW.md`
- Architecture: `/docs/ARCHITECTURE_PHASE2.md`
- Migrations: `supabase/migrations/`
- Python Loader: `supabase/scripts/load_csv_data.py`

---

**Status:** ✅ PRONTO PARA IMPLEMENTAÇÃO
**Próximo Responsável:** @dev (Dex) - Backend & Frontend Integration

---

*Implementation Guide preparado por Dara (Data Engineer) - 2026-02-21*

# Huli Automations Hub - Mission Control

Centralized dashboard for monitoring and controlling daily automation scripts.

## 🎯 Overview

**Huli Automations Hub** is an independent job orchestration system that replaces OpenClaw dependency. It provides:

- ✅ **4 Scheduled Jobs** - Automated execution at specific times
- ✅ **Real-time Dashboard** - Monitor job status and execution history
- ✅ **Manual Execution** - Trigger jobs on demand
- ✅ **Structured Logging** - JSON formatted execution logs
- ✅ **Health Monitoring** - API health check endpoint

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip/venv
- Git (optional)

### Setup

1. **Clone repository:**
   ```bash
   cd /Users/matheusribeiro/Desktop/HULI-VELL
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Setup environment:**
   ```bash
   # Copy the example .env file
   cp backend/.env.example .env

   # Edit .env with your credentials
   vim .env  # or your favorite editor
   ```

5. **Copy job scripts** (if not already in place):
   ```bash
   # Scripts should be in jobs/ directory
   # Expected files:
   # - jobs/facebook_ads_to_sheets.py
   # - jobs/hotmart_to_sheets.py
   # - jobs/huli_consolidator.py
   # - jobs/analisar_funis.py
   ```

6. **Run the application:**
   ```bash
   python3 backend/main.py
   ```

7. **Access dashboard:**
   - Open browser: http://localhost:8000
   - API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## 📋 Configuration

### Environment Variables (.env)

**Application:**
- `ENVIRONMENT` - development or production
- `DEBUG` - true/false
- `LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR, CRITICAL

**Server:**
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)

**Scheduler:**
- `SCHEDULER_ENABLED` - true/false (default: true)
- `JOBS_CONFIG_PATH` - Path to jobs config JSON
- `DEFAULT_JOB_TIMEOUT` - Timeout in seconds (default: 300)

**Credentials:**
- `HOTMART_CLIENT_ID`
- `HOTMART_CLIENT_SECRET`
- `HOTMART_BASIC_TOKEN`
- `FACEBOOK_ACCESS_TOKEN`
- `FACEBOOK_SHEET_ID`
- `GOOGLE_CREDENTIALS_PATH`

See `backend/.env.example` for complete list.

### Jobs Configuration (jobs_config.json)

Jobs are defined in `backend/config/jobs_config.json`:

```json
{
  "jobs": [
    {
      "id": "facebook-ads",
      "name": "Facebook Ads Daily Extraction",
      "script": "jobs/facebook_ads_to_sheets.py",
      "schedule": "0 6 * * *",
      "timeout": 300,
      "retries": 0
    }
  ]
}
```

**Schedule Format (Cron):**
- `0 6 * * *` - Daily at 06:00 AM
- `15 6 * * *` - Daily at 06:15 AM
- `45 6 * * *` - Daily at 06:45 AM
- `0 7 * * 3` - Weekly on Wednesday at 07:00 AM

## 📡 API Endpoints

### Jobs

**GET /api/jobs**
- List all scheduled jobs with current status
- Response: JSON array with job details

**GET /api/jobs/{id}**
- Get status of specific job
- Response: Job details

### Logs

**GET /api/jobs/{id}/logs?limit=10**
- Get execution logs for a job
- Parameters:
  - `limit` - Number of logs (default: 10)
- Response: List of logs with timestamps, status, output

### Execution

**POST /api/jobs/{id}/execute**
- Manually trigger a job
- Response: Execution status

### Health

**GET /health**
- Health check endpoint
- Response: System status

## 🖥️ Frontend

### Dashboard Features

- **Job Cards** - Shows job status, next run time, last execution
- **Execute Now Button** - Manually trigger any job
- **Log Viewer** - See execution history
- **Auto-Refresh** - Updates every 30 seconds
- **Responsive Design** - Works on desktop, tablet, mobile

### Technology

- HTML5
- CSS3 (vanilla)
- JavaScript (vanilla, no frameworks)

## 📂 Project Structure

```
huli-automations-hub/
├── backend/
│   ├── main.py                      # FastAPI application
│   ├── config/
│   │   ├── config.py                # Configuration management
│   │   └── jobs_config.json         # Job definitions
│   ├── scheduler/
│   │   └── job_scheduler.py         # APScheduler integration
│   ├── services/
│   │   ├── execution_service.py     # Subprocess execution
│   │   └── logging_service.py       # JSON logging
│   ├── api/
│   │   ├── jobs.py                  # Job endpoints
│   │   └── logs.py                  # Logs & execution endpoints
│   ├── models/
│   │   └── job.py                   # Pydantic models
│   ├── requirements.txt             # Python dependencies
│   └── .env.example                 # Environment template
├── frontend/
│   ├── index.html                   # Dashboard HTML
│   ├── style.css                    # Styling
│   └── app.js                       # JavaScript logic
├── jobs/                            # Python automation scripts
│   ├── facebook_ads_to_sheets.py
│   ├── hotmart_to_sheets.py
│   ├── huli_consolidator.py
│   └── analisar_funis.py
├── logs/                            # Execution logs (generated)
├── README.md                        # This file
└── .gitignore                       # Git ignore rules
```

## 🔧 Technical Details

### Timezone Handling

All timestamps use **America/Sao_Paulo** timezone. This is hardcoded in `config.py` and critical for accurate scheduling.

### Logging

Execution logs are stored as JSON files:
- One file per job per day
- Format: `{job_id}_YYYY-MM-DD.json`
- Latest 100 executions kept per job
- Location: `./logs/` directory

### Error Handling

- Job failures don't stop the scheduler
- Errors are logged with full stack trace
- Dashboard displays error status
- Timeout handling: configurable per job

### Performance

- Lightweight async framework (FastAPI)
- No database - JSON file storage
- Dashboard auto-refresh every 30 seconds
- Efficient subprocess execution

## 🧪 Testing

### Manual Testing

```bash
# Test scheduler startup
python3 -c "from backend.scheduler.job_scheduler import get_scheduler; s = get_scheduler(); print(f'Jobs: {len(s.job_configs)}')"

# Test execution service
python3 -c "from backend.services.execution_service import get_execution_service; e = get_execution_service(); print('Execution service OK')"

# Test logging service
python3 -c "from backend.services.logging_service import get_logging_service; l = get_logging_service(); print('Logging service OK')"
```

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# List jobs
curl http://localhost:8000/api/jobs

# Get job logs
curl http://localhost:8000/api/jobs/facebook-ads/logs

# Execute job manually
curl -X POST http://localhost:8000/api/jobs/facebook-ads/execute
```

## 🔐 Security

**Important Security Notes:**

1. `.env` file contains credentials - **NEVER commit to git**
2. Use `.env.example` as template for new installations
3. Keep `logs/` directory secure (contains execution history)
4. In production, use proper secrets management (environment variables, secret manager)
5. Consider adding authentication to dashboard if exposed publicly

## 🚀 Deployment

### Local Development

```bash
python3 backend/main.py
```

### Production (with Supervisor/Systemd)

```bash
# Example supervisor configuration
[program:huli-automations]
command=/path/to/venv/bin/python /path/to/backend/main.py
directory=/path/to/project
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/huli-automations.log
```

## 📊 Monitoring

### Health Check

The `/health` endpoint provides system status:

```json
{
  "status": "ok",
  "app": "Huli Automations Hub - Mission Control",
  "version": "1.0.0",
  "scheduler": "running",
  "jobs_count": 4
}
```

### Log Files

Check logs in `logs/` directory:
- `facebook-ads_2026-02-20.json`
- `hotmart_2026-02-20.json`
- `consolidator_2026-02-20.json`
- `analise-funis_2026-02-26.json`

## 🐛 Troubleshooting

### Scheduler not starting

1. Check `SCHEDULER_ENABLED` in `.env` is `true`
2. Verify `jobs_config.json` path is correct
3. Check logs for startup errors

### Jobs not executing

1. Verify script files exist in `jobs/` directory
2. Check job script has execute permissions
3. Verify `.env` credentials are correct
4. Check system timezone matches configured timezone

### Dashboard not updating

1. Verify scheduler is running (green indicator)
2. Check browser console for JavaScript errors
3. Verify API endpoints are accessible

## 📚 References

- **FastAPI:** https://fastapi.tiangolo.com/
- **APScheduler:** https://apscheduler.readthedocs.io/
- **Uvicorn:** https://www.uvicorn.org/
- **Pydantic:** https://docs.pydantic.dev/

## 📝 License

Internal use - Huli Inc.

## 👥 Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs in `logs/` directory
3. Contact development team

---

**Last Updated:** 2026-02-20
**Version:** 1.0.0
**Status:** MVP Ready

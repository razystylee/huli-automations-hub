"""
Huli-VELLHUB

FastAPI application for orchestrating and monitoring automation jobs
"""

import logging
import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.config.config import config
from backend.scheduler.job_scheduler import get_scheduler
from backend.services.execution_service import get_execution_service
from backend.services.logging_service import get_logging_service
from backend.services.supabase_service import get_supabase_service
from backend.api import jobs, logs, analytics

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="Centralized dashboard for monitoring and controlling daily automation scripts",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(jobs.router)
app.include_router(logs.router)
app.include_router(analytics.router)


@app.get("/health")
async def health():
    """Health check endpoint"""
    scheduler = get_scheduler()
    status = scheduler.get_scheduler_status()

    return {
        "status": "ok",
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "scheduler": status.get("status"),
        "jobs_count": status.get("jobs_count"),
    }


# Mount frontend static files (must be AFTER API routers and endpoints)
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


@app.on_event("startup")
async def startup_event():
    """Initialize scheduler and services on application startup"""
    logger.info(f"Starting {config.APP_NAME}...")

    try:
        # Initialize scheduler
        scheduler = get_scheduler()

        # Load job configuration
        if not scheduler.load_jobs_config(config.JOBS_CONFIG_PATH):
            logger.error("Failed to load jobs configuration")
            return

        # Initialize execution service
        execution_service = get_execution_service(
            base_path=str(Path(__file__).parent.parent)
        )

        # Initialize logging service
        logging_service = get_logging_service()

        # Initialize Supabase service (optional - log warning if fails)
        supabase_service = None
        try:
            supabase_service = get_supabase_service()
            logger.info("Supabase service initialized successfully")
        except ValueError as e:
            logger.warning(f"Supabase service not configured: {e}. Analytics endpoints will not work.")

        # Set execution callback
        def execute_job_callback(job_id: str, job) -> None:
            """Callback function for job execution"""
            logger.info(f"Executing job: {job.name} (id={job_id})")
            result = execution_service.execute_script(job.script, timeout=job.timeout)

            # Log execution to local JSON file
            logging_service.log_execution(job_id, result)

            # Log execution to Supabase (if available)
            if supabase_service:
                try:
                    supabase_service.log_execution(job_id, job.name, result)
                except Exception as e:
                    logger.warning(f"Failed to log execution to Supabase: {e}")

            # Update scheduler state
            scheduler.update_job_state(job_id, result.status, result.timestamp)

            # Log summary
            summary = execution_service.get_execution_summary(result)
            logger.info(f"Job '{job.name}' {summary}")

        scheduler.set_execution_callback(execute_job_callback)

        # Start scheduler
        if config.SCHEDULER_ENABLED:
            if scheduler.start():
                logger.info("Scheduler started successfully")
            else:
                logger.error("Failed to start scheduler")
        else:
            logger.info("Scheduler is disabled (SCHEDULER_ENABLED=false)")

    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down...")

    try:
        scheduler = get_scheduler()
        if scheduler.stop():
            logger.info("Scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Root endpoint is served by StaticFiles (index.html)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower(),
    )

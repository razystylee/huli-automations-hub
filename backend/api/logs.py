"""
Logs and Execution API Routes

Endpoints for viewing execution logs and manually triggering jobs
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from backend.scheduler.job_scheduler import get_scheduler
from backend.services.logging_service import get_logging_service
from backend.services.execution_service import get_execution_service
from backend.models.job import JobExecutionResponse, JobStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["logs", "execution"])


@router.get("/{job_id}/logs")
async def get_job_logs(job_id: str, limit: Optional[int] = 10):
    """
    Get execution logs for a specific job

    Args:
        job_id: Job identifier
        limit: Maximum number of logs to return (default: 10)

    Returns:
        List of execution logs with timestamp, status, duration, output
    """
    try:
        scheduler = get_scheduler()

        # Verify job exists
        if job_id not in scheduler.job_configs:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

        logging_service = get_logging_service()
        logs = logging_service.get_job_logs(job_id, limit=limit)

        return {
            "job_id": job_id,
            "logs_count": len(logs),
            "logs": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "status": log.status.value,
                    "duration": log.duration,
                    "output": log.output,
                    "errors": log.errors,
                }
                for log in logs
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting logs for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")


@router.post("/{job_id}/execute")
async def execute_job(job_id: str):
    """
    Manually trigger execution of a job

    Args:
        job_id: Job identifier

    Returns:
        Response with job status and execution confirmation
    """
    try:
        scheduler = get_scheduler()

        # Verify job exists
        if job_id not in scheduler.job_configs:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

        job = scheduler.job_configs[job_id]

        logger.info(f"Manual execution triggered for job: {job_id}")

        # Execute job synchronously
        execution_service = get_execution_service()
        result = execution_service.execute_script(job.script, timeout=job.timeout)

        # Log the execution
        logging_service = get_logging_service()
        logging_service.log_execution(job_id, result)

        # Update scheduler state
        scheduler.update_job_state(job_id, result.status, result.timestamp)

        return JobExecutionResponse(
            id=job_id, status=result.status, message="Job execution completed"
        ).model_dump()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error executing job: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint

    Returns:
        Status of application, scheduler, and job configuration
    """
    try:
        scheduler = get_scheduler()
        scheduler_status = scheduler.get_scheduler_status()

        return {
            "status": "ok",
            "scheduler": scheduler_status.get("status", "unknown"),
            "jobs_scheduled": scheduler_status.get("jobs_count", 0),
            "jobs_config_loaded": len(scheduler.job_configs) > 0,
        }

    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

"""
Jobs API Routes

Endpoints for listing jobs and retrieving job status
"""

import logging
from typing import List
from datetime import datetime

from fastapi import APIRouter, HTTPException

from backend.scheduler.job_scheduler import get_scheduler
from backend.models.job import Job

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobStatusResponse:
    """Response model for job with current status"""

    def __init__(self, job: Job, scheduler):
        self.id = job.id
        self.name = job.name
        self.script = job.script
        self.schedule = job.schedule
        self.timeout = job.timeout

        # Get current state from scheduler
        state = scheduler.get_job_state(job.id)
        self.last_run = state.last_run_time.isoformat() if state.last_run_time else None
        self.last_status = state.last_run_status.value if state.last_run_status else None
        self.is_running = state.is_running

        # Get next_run_time directly from APScheduler (always current, not cached)
        self.next_run = None
        if scheduler.scheduler and scheduler.scheduler.running:
            for scheduled_job in scheduler.scheduler.get_jobs():
                if scheduled_job.id == job.id:
                    self.next_run = scheduled_job.next_run_time.isoformat() if scheduled_job.next_run_time else None
                    break

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "script": self.script,
            "schedule": self.schedule,
            "timeout": self.timeout,
            "next_run": self.next_run,
            "last_run": self.last_run,
            "last_status": self.last_status,
            "is_running": self.is_running,
        }


@router.get("")
async def list_jobs():
    """
    List all scheduled jobs with current status

    Returns:
        JSON list of jobs with next run time, last execution status, etc
    """
    try:
        scheduler = get_scheduler()

        jobs_response = []
        for job_id, job in scheduler.job_configs.items():
            job_status = JobStatusResponse(job, scheduler)
            jobs_response.append(job_status.to_dict())

        return {"jobs": jobs_response, "count": len(jobs_response)}

    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing jobs: {str(e)}")


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    """
    Get detailed status of a specific job

    Args:
        job_id: Job identifier

    Returns:
        Job details with current status and execution history
    """
    try:
        scheduler = get_scheduler()

        job = scheduler.job_configs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

        job_status = JobStatusResponse(job, scheduler)
        return job_status.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting job status: {str(e)}")

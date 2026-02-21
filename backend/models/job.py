"""
Job models and data structures for Huli Automations Hub

Defines Pydantic models for Job, JobStatus, and JobLog entities.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Enum for job execution status"""

    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    RUNNING = "RUNNING"


class JobLog(BaseModel):
    """Model for individual job execution log"""

    timestamp: datetime = Field(..., description="Execution timestamp (ISO 8601)")
    status: JobStatus = Field(..., description="Execution status")
    duration: float = Field(..., description="Execution duration in seconds")
    output: Optional[str] = Field(None, description="Standard output from job execution")
    errors: Optional[str] = Field(None, description="Standard error from job execution")


class Job(BaseModel):
    """Model for a scheduled job"""

    id: str = Field(..., description="Unique job identifier")
    name: str = Field(..., description="Human-readable job name")
    script: str = Field(..., description="Path to Python script to execute")
    schedule: str = Field(..., description="Cron expression for scheduling")
    timeout: int = Field(default=300, description="Execution timeout in seconds")
    retries: int = Field(default=0, description="Number of retries on failure")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "facebook-ads",
                "name": "Facebook Ads Daily Extraction",
                "script": "jobs/facebook_ads_to_sheets.py",
                "schedule": "0 6 * * *",
                "timeout": 300,
                "retries": 0,
            }
        }


class JobWithLogs(BaseModel):
    """Job with associated logs"""

    job: Job
    logs: List[JobLog] = Field(default_factory=list, description="List of execution logs")
    next_run: Optional[datetime] = Field(None, description="Next scheduled execution time")
    last_run: Optional[datetime] = Field(None, description="Last execution time")
    last_status: Optional[JobStatus] = Field(None, description="Last execution status")


class JobExecutionRequest(BaseModel):
    """Request to manually execute a job"""

    job_id: str = Field(..., description="ID of job to execute")


class JobExecutionResponse(BaseModel):
    """Response after job execution request"""

    id: str = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Current status")
    message: str = Field(..., description="Response message")

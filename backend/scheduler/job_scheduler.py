"""
Job Scheduler Service

Manages APScheduler configuration and scheduling of all automation jobs.
Handles job state tracking and execution wrapper functions.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone as pytz_timezone

from backend.config.config import config
from backend.models.job import Job, JobStatus

logger = logging.getLogger(__name__)


class JobState:
    """Track state of a scheduled job"""

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.is_running = False
        self.last_run_status: Optional[JobStatus] = None
        self.last_run_time: Optional[datetime] = None
        self.next_run_time: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert state to dictionary"""
        return {
            "job_id": self.job_id,
            "is_running": self.is_running,
            "last_run_status": self.last_run_status,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "next_run_time": self.next_run_time.isoformat() if self.next_run_time else None,
        }


class JobScheduler:
    """
    Manages job scheduling with APScheduler

    Responsible for:
    - Loading job configuration from JSON
    - Creating and managing APScheduler instances
    - Scheduling jobs with proper timezone handling
    - Tracking job state and execution status
    """

    def __init__(self):
        self.scheduler: Optional[BackgroundScheduler] = None
        self.tz = pytz_timezone(config.TIMEZONE)
        self.job_configs: Dict[str, Job] = {}
        self.job_states: Dict[str, JobState] = {}
        self.execution_callback: Optional[Callable] = None

    def load_jobs_config(self, config_path: str) -> bool:
        """
        Load job configuration from JSON file

        Args:
            config_path: Path to jobs_config.json

        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                logger.error(f"Jobs config file not found: {config_path}")
                return False

            with open(config_file, "r") as f:
                data = json.load(f)

            self.job_configs = {}
            for job_data in data.get("jobs", []):
                job = Job(**job_data)
                self.job_configs[job.id] = job
                self.job_states[job.id] = JobState(job.id)

            logger.info(f"Loaded {len(self.job_configs)} jobs from config")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in jobs config: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading jobs config: {e}")
            return False

    def set_execution_callback(self, callback: Callable) -> None:
        """
        Set callback function to execute when job runs

        Args:
            callback: Callable that will be invoked with (job_id, job) parameters
        """
        self.execution_callback = callback

    def start(self) -> bool:
        """
        Start the scheduler and schedule all jobs

        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            if not self.job_configs:
                logger.error("No jobs to schedule. Load config first.")
                return False

            # Create scheduler with timezone
            self.scheduler = BackgroundScheduler(timezone=self.tz)

            # Schedule each job
            for job_id, job in self.job_configs.items():
                self._schedule_job(job_id, job)

            # Start scheduler
            self.scheduler.start()
            logger.info(f"Scheduler started with {len(self.job_configs)} jobs")
            return True

        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            return False

    def stop(self) -> bool:
        """
        Stop the scheduler

        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            if self.scheduler:
                self.scheduler.shutdown(wait=False)
                logger.info("Scheduler stopped")
                return True
            return False
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
            return False

    def _schedule_job(self, job_id: str, job: Job) -> None:
        """
        Schedule a single job with APScheduler

        Args:
            job_id: Unique job identifier
            job: Job configuration
        """
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")

        try:
            # Create cron trigger from schedule expression
            trigger = CronTrigger.from_crontab(job.schedule, timezone=self.tz)

            # Create wrapper function that captures job context
            def job_wrapper():
                self._execute_job(job_id, job)

            # Add job to scheduler
            scheduled_job = self.scheduler.add_job(
                job_wrapper,
                trigger=trigger,
                id=job_id,
                name=job.name,
                replace_existing=True,
            )

            # Update next run time (safe check for when scheduler not fully started)
            if hasattr(scheduled_job, 'next_run_time') and scheduled_job.next_run_time:
                self.job_states[job_id].next_run_time = scheduled_job.next_run_time

            logger.info(
                f"Scheduled job '{job.name}' (id={job_id}) with cron: {job.schedule}"
            )

        except Exception as e:
            logger.error(f"Error scheduling job {job_id}: {e}")

    def _execute_job(self, job_id: str, job: Job) -> None:
        """
        Execute a job through the execution callback

        Args:
            job_id: Job identifier
            job: Job configuration
        """
        state = self.job_states.get(job_id)
        if not state:
            logger.error(f"Job state not found for {job_id}")
            return

        state.is_running = True
        logger.info(f"Job '{job.name}' started")

        try:
            if self.execution_callback:
                self.execution_callback(job_id, job)
        except Exception as e:
            logger.error(f"Error executing job {job_id}: {e}")
        finally:
            state.is_running = False

    def get_job_state(self, job_id: str) -> Optional[JobState]:
        """
        Get current state of a job

        Args:
            job_id: Job identifier

        Returns:
            JobState if found, None otherwise
        """
        return self.job_states.get(job_id)

    def get_all_job_states(self) -> Dict[str, JobState]:
        """
        Get states of all jobs

        Returns:
            Dictionary of job_id -> JobState
        """
        return dict(self.job_states)

    def update_job_state(
        self, job_id: str, status: JobStatus, run_time: datetime
    ) -> None:
        """
        Update job execution state

        Args:
            job_id: Job identifier
            status: Execution status
            run_time: Execution timestamp
        """
        state = self.job_states.get(job_id)
        if state:
            state.last_run_status = status
            state.last_run_time = run_time
            logger.debug(
                f"Updated state for job {job_id}: status={status}, time={run_time}"
            )

    def get_scheduler_status(self) -> dict:
        """
        Get overall scheduler status

        Returns:
            Dictionary with scheduler information
        """
        if not self.scheduler:
            return {"status": "stopped", "jobs_count": 0}

        return {
            "status": "running" if self.scheduler.running else "stopped",
            "jobs_count": len(self.scheduler.get_jobs()),
            "timezone": str(self.tz),
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                }
                for job in self.scheduler.get_jobs()
            ],
        }


# Global scheduler instance
_scheduler_instance: Optional[JobScheduler] = None


def get_scheduler() -> JobScheduler:
    """
    Get or create the global scheduler instance

    Returns:
        JobScheduler instance
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = JobScheduler()
    return _scheduler_instance

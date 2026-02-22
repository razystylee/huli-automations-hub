"""
Job Logging Service

Handles structured JSON logging for job execution with:
- Per-job log files (hotmart_YYYY-MM-DD.json, etc)
- Log rotation (keep last 100 entries)
- JSON structured logs with precise timestamps
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from backend.config.config import config
from backend.models.job import JobLog, JobStatus
from backend.services.execution_service import ExecutionResult

logger = logging.getLogger(__name__)


class LoggingService:
    """
    Service for structured logging of job executions

    Responsible for:
    - Writing execution results to JSON log files
    - Maintaining log rotation (keep last 100 entries)
    - Reading logs for dashboard display
    - Organizing logs by job_id
    """

    def __init__(self, logs_dir: Optional[str] = None):
        """
        Initialize logging service

        Args:
            logs_dir: Directory where logs will be stored
        """
        self.logs_dir = Path(logs_dir) if logs_dir else Path(config.LOGS_DIR)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.max_logs_per_job = 100

    def log_execution(self, job_id: str, result: ExecutionResult) -> bool:
        """
        Log a job execution result to JSON file

        Args:
            job_id: Job identifier
            result: ExecutionResult from execution service

        Returns:
            bool: True if logged successfully, False otherwise
        """
        try:
            # Load existing logs
            logs = self.get_job_logs(job_id)

            # Convert execution result to JobLog
            job_log = JobLog(
                timestamp=result.timestamp,
                status=result.status,
                duration=result.duration,
                output=result.stdout,
                errors=result.stderr if result.stderr else (result.error or None),
            )

            # Add new log
            logs.append(job_log)

            # Keep only last N logs
            if len(logs) > self.max_logs_per_job:
                logs = logs[-self.max_logs_per_job :]

            # Write back to file
            return self._write_logs(job_id, logs)

        except Exception as e:
            logger.error(f"Error logging execution for job {job_id}: {e}")
            return False

    def get_job_logs(
        self, job_id: str, limit: Optional[int] = None
    ) -> List[JobLog]:
        """
        Get execution logs for a specific job

        Args:
            job_id: Job identifier
            limit: Maximum number of logs to return (None for all)

        Returns:
            List of JobLog objects (most recent first)
        """
        log_file = self._get_log_file_path(job_id)

        if not log_file.exists():
            return []

        try:
            with open(log_file, "r") as f:
                data = json.load(f)

            logs = [JobLog(**log_entry) for log_entry in data.get("logs", [])]

            # Return most recent first
            logs.reverse()

            # Apply limit if specified
            if limit:
                logs = logs[:limit]

            return logs

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error reading logs for job {job_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error reading logs for job {job_id}: {e}")
            return []

    def get_last_log(self, job_id: str) -> Optional[JobLog]:
        """
        Get the most recent log entry for a job

        Args:
            job_id: Job identifier

        Returns:
            Most recent JobLog or None if no logs exist
        """
        logs = self.get_job_logs(job_id, limit=1)
        return logs[0] if logs else None

    def get_all_job_ids(self) -> List[str]:
        """
        Get all job IDs that have logs

        Returns:
            List of job IDs with existing logs
        """
        job_ids = set()

        for log_file in self.logs_dir.glob("*.json"):
            job_id = self._extract_job_id_from_filename(log_file.name)
            if job_id:
                job_ids.add(job_id)

        return sorted(list(job_ids))

    def clear_old_logs(self, days: int = 30) -> int:
        """
        Delete log files older than specified days

        Args:
            days: Delete logs older than this many days

        Returns:
            Number of files deleted
        """
        from datetime import timedelta

        threshold_time = datetime.now(config.TZ) - timedelta(days=days)
        deleted_count = 0

        try:
            for log_file in self.logs_dir.glob("*.json"):
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime, tz=config.TZ)

                if file_mtime < threshold_time:
                    log_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old log file: {log_file.name}")

            return deleted_count

        except Exception as e:
            logger.error(f"Error clearing old logs: {e}")
            return 0

    def _write_logs(self, job_id: str, logs: List[JobLog]) -> bool:
        """
        Write logs to JSON file

        Args:
            job_id: Job identifier
            logs: List of JobLog objects

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            log_file = self._get_log_file_path(job_id)

            # Convert logs to dict format
            logs_data = {
                "job_id": job_id,
                "updated_at": datetime.now(config.TZ).isoformat(),
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

            # Write to file with pretty formatting
            with open(log_file, "w") as f:
                json.dump(logs_data, f, indent=2)

            logger.debug(f"Logged execution for job {job_id} to {log_file}")
            return True

        except Exception as e:
            logger.error(f"Error writing logs for job {job_id}: {e}")
            return False

    def _get_log_file_path(self, job_id: str) -> Path:
        """
        Get the log file path for a job

        Args:
            job_id: Job identifier

        Returns:
            Path to log file
        """
        # Format: {job_id}_YYYY-MM-DD.json
        today = datetime.now(config.TZ).strftime("%Y-%m-%d")
        filename = f"{job_id}_{today}.json"
        return self.logs_dir / filename

    @staticmethod
    def _extract_job_id_from_filename(filename: str) -> Optional[str]:
        """
        Extract job_id from log filename

        Args:
            filename: Filename like 'hotmart_2026-02-20.json'

        Returns:
            Job ID or None if invalid format
        """
        if not filename.endswith(".json"):
            return None

        # Remove .json extension
        name_without_ext = filename[:-5]

        # Split by last underscore to handle job IDs with underscores
        parts = name_without_ext.rsplit("_", 1)
        if len(parts) == 2 and parts[1].count("-") == 2:
            # parts[1] looks like a date YYYY-MM-DD
            return parts[0]

        return None


# Global logging service instance
_logging_service: Optional[LoggingService] = None


def get_logging_service(logs_dir: Optional[str] = None) -> LoggingService:
    """
    Get or create the global logging service instance

    Args:
        logs_dir: Directory where logs will be stored

    Returns:
        LoggingService instance
    """
    global _logging_service
    if _logging_service is None:
        _logging_service = LoggingService(logs_dir)
    return _logging_service

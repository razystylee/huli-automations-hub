"""
Job Execution Service

Handles subprocess execution of Python scripts with:
- stdout/stderr capture
- Timeout handling
- Error handling
- Execution time tracking
"""

import os
import subprocess
import logging
import time
from datetime import datetime
from typing import Tuple, Optional
from pathlib import Path

from backend.config.config import config
from backend.models.job import JobStatus

logger = logging.getLogger(__name__)


class ExecutionResult:
    """Result of a job execution"""

    def __init__(
        self,
        status: JobStatus,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        duration: float = 0.0,
        error: Optional[str] = None,
    ):
        self.status = status
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration
        self.error = error
        self.timestamp = datetime.now(config.TZ)

    def to_dict(self) -> dict:
        """Convert result to dictionary"""
        return {
            "status": self.status.value,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration": round(self.duration, 2),
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


class ExecutionService:
    """
    Service for executing Python scripts as subprocesses

    Responsible for:
    - Running Python scripts in isolated subprocesses
    - Capturing and logging output
    - Handling timeouts and errors
    - Tracking execution metrics
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize execution service

        Args:
            base_path: Base directory for resolving relative script paths
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()

    def execute_script(
        self, script_path: str, timeout: int = 300, env: Optional[dict] = None
    ) -> ExecutionResult:
        """
        Execute a Python script in a subprocess

        Args:
            script_path: Path to Python script (relative or absolute)
            timeout: Execution timeout in seconds
            env: Environment variables to pass to subprocess

        Returns:
            ExecutionResult with status, output, and metrics
        """
        # Resolve script path
        full_script_path = self._resolve_script_path(script_path)

        if not full_script_path:
            return ExecutionResult(
                status=JobStatus.ERROR,
                error=f"Script not found: {script_path}",
            )

        logger.info(f"Executing script: {full_script_path}")

        start_time = time.time()

        try:
            # Run subprocess with timeout and output capture
            # Prepare environment: merge provided env with current environment
            subprocess_env = os.environ.copy()
            if env:
                subprocess_env.update(env)

            result = subprocess.run(
                ["python3", str(full_script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=subprocess_env,
            )

            duration = time.time() - start_time

            # Determine status based on return code
            if result.returncode == 0:
                status = JobStatus.SUCCESS
                logger.info(
                    f"Script completed successfully in {duration:.2f}s: {full_script_path}"
                )
            else:
                status = JobStatus.ERROR
                logger.error(
                    f"Script failed with code {result.returncode}: {full_script_path}"
                )

            return ExecutionResult(
                status=status,
                stdout=result.stdout,
                stderr=result.stderr,
                duration=duration,
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            error_msg = f"Script execution timed out after {timeout}s"
            logger.error(f"{error_msg}: {full_script_path}")

            return ExecutionResult(
                status=JobStatus.ERROR,
                error=error_msg,
                duration=duration,
            )

        except FileNotFoundError:
            duration = time.time() - start_time
            error_msg = f"Python interpreter not found"
            logger.error(f"{error_msg}: {full_script_path}")

            return ExecutionResult(
                status=JobStatus.ERROR,
                error=error_msg,
                duration=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            logger.error(f"Unexpected error executing script: {e}")

            return ExecutionResult(
                status=JobStatus.ERROR,
                error=error_msg,
                duration=duration,
            )

    def _resolve_script_path(self, script_path: str) -> Optional[Path]:
        """
        Resolve script path to absolute path

        Args:
            script_path: Path to script (relative or absolute)

        Returns:
            Resolved Path if exists, None otherwise
        """
        # If absolute path, use as-is
        if Path(script_path).is_absolute():
            path = Path(script_path)
        else:
            # Relative path: resolve from base_path
            path = self.base_path / script_path

        if path.exists() and path.is_file():
            return path.resolve()

        logger.warning(f"Script path does not exist or is not a file: {path}")
        return None

    @staticmethod
    def get_execution_summary(result: ExecutionResult) -> str:
        """
        Generate a summary of execution result

        Args:
            result: ExecutionResult

        Returns:
            Summary string
        """
        if result.status == JobStatus.SUCCESS:
            return f"✅ SUCCESS in {result.duration:.2f}s"
        else:
            return f"❌ ERROR ({result.error}) after {result.duration:.2f}s"


# Global execution service instance
_execution_service: Optional[ExecutionService] = None


def get_execution_service(base_path: Optional[str] = None) -> ExecutionService:
    """
    Get or create the global execution service instance

    Args:
        base_path: Base directory for resolving relative script paths

    Returns:
        ExecutionService instance
    """
    global _execution_service
    if _execution_service is None:
        _execution_service = ExecutionService(base_path)
    return _execution_service

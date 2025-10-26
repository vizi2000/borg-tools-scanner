"""
Agent Zero Bridge - HTTP client for Agent Zero on borg.tools:50001

Provides interface to submit tasks and retrieve results from Agent Zero agent.
Supports code audits, security scans, and custom task definitions.

Created by The Collective Borg.tools
"""

import requests
import time
import logging
from typing import Dict, Optional, Any, List
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class AgentZeroError(Exception):
    """Base exception for Agent Zero Bridge errors."""
    pass


class ConnectionError(AgentZeroError):
    """Raised when connection to Agent Zero fails."""
    pass


class TaskSubmissionError(AgentZeroError):
    """Raised when task submission fails."""
    pass


class TaskResultError(AgentZeroError):
    """Raised when retrieving task results fails."""
    pass


class AgentZeroBridge:
    """
    HTTP client for Agent Zero running on borg.tools:50001.

    Features:
    - Submit tasks to Agent Zero (code audits, security scans, custom tasks)
    - Poll for task completion with configurable timeout
    - Graceful error handling with fallback options
    - Connection verification

    Example:
        bridge = AgentZeroBridge()
        task_id = bridge.submit_task('/path/to/project', 'code_audit')
        result = bridge.get_result(task_id)
        print(result)
    """

    DEFAULT_BASE_URL = 'http://borg.tools:50001'
    DEFAULT_TIMEOUT = 120  # seconds per request
    DEFAULT_POLL_INTERVAL = 5  # seconds between status checks
    MAX_POLL_ATTEMPTS = 60  # max number of polling attempts (5 min total)

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        poll_interval: int = DEFAULT_POLL_INTERVAL
    ):
        """
        Initialize Agent Zero Bridge.

        Args:
            base_url: Base URL of Agent Zero API (default: http://borg.tools:50001)
            timeout: Request timeout in seconds (default: 120)
            poll_interval: Polling interval in seconds (default: 5)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Borg.tools-Scanner/1.0',
            'Content-Type': 'application/json'
        })

        logger.info(f"🔌 Agent Zero Bridge initialized: {self.base_url}")

    def health_check(self) -> Dict[str, Any]:
        """
        Check Agent Zero health status.

        Returns:
            Dict with health status information

        Raises:
            ConnectionError: If connection fails
        """
        try:
            logger.info("🔌 Testing connection to borg.tools:50001...")
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            logger.info("✅ Connection verified, Agent Zero is healthy")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Connection failed: {e}")
            raise ConnectionError(f"Failed to connect to Agent Zero: {e}")

    def submit_task(
        self,
        project_path: str,
        task_type: str,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Submit a task to Agent Zero.

        Args:
            project_path: Absolute path to project directory
            task_type: Type of task ('code_audit', 'security_scan', 'custom')
            additional_params: Optional additional parameters for the task

        Returns:
            Task ID string for polling results

        Raises:
            TaskSubmissionError: If task submission fails
        """
        project_path = Path(project_path).absolute()

        if not project_path.exists():
            raise TaskSubmissionError(f"Project path does not exist: {project_path}")

        payload = {
            'project_path': str(project_path),
            'task_type': task_type,
            'timestamp': time.time()
        }

        if additional_params:
            payload.update(additional_params)

        try:
            logger.info(f"📡 Submitting task to Agent Zero: {task_type} for {project_path}")
            response = self.session.post(
                f"{self.base_url}/api/task",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            task_id = result.get('task_id')

            if not task_id:
                raise TaskSubmissionError("No task_id in response")

            logger.info(f"✅ Task submitted successfully: {task_id}")
            return task_id

        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Task submission timeout after {self.timeout}s")
            raise TaskSubmissionError(f"Task submission timeout after {self.timeout}s")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Task submission failed: {e}")
            raise TaskSubmissionError(f"Failed to submit task: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON response: {e}")
            raise TaskSubmissionError(f"Invalid JSON response from Agent Zero: {e}")

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get current status of a task.

        Args:
            task_id: Task ID to check

        Returns:
            Dict with task status information

        Raises:
            TaskResultError: If status check fails
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/task/{task_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get task status: {e}")
            raise TaskResultError(f"Failed to get task status: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON response: {e}")
            raise TaskResultError(f"Invalid JSON response: {e}")

    def get_result(
        self,
        task_id: str,
        poll: bool = True,
        max_attempts: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get result of a submitted task, with optional polling.

        Args:
            task_id: Task ID to retrieve results for
            poll: Whether to poll until completion (default: True)
            max_attempts: Max polling attempts (default: MAX_POLL_ATTEMPTS)

        Returns:
            Dict with task results and metadata

        Raises:
            TaskResultError: If result retrieval fails or times out
        """
        if max_attempts is None:
            max_attempts = self.MAX_POLL_ATTEMPTS

        if not poll:
            return self.get_task_status(task_id)

        logger.info(f"🔄 Polling for task completion: {task_id}")

        for attempt in range(max_attempts):
            try:
                status_data = self.get_task_status(task_id)
                status = status_data.get('status', 'unknown')

                if status == 'completed':
                    logger.info(f"✅ Task completed: {task_id}")
                    return status_data
                elif status == 'failed':
                    error = status_data.get('error', 'Unknown error')
                    logger.error(f"❌ Task failed: {error}")
                    return status_data
                elif status in ['pending', 'running', 'in_progress']:
                    logger.debug(f"⏳ Task {status}, attempt {attempt + 1}/{max_attempts}")
                    time.sleep(self.poll_interval)
                else:
                    logger.warning(f"⚠️ Unknown task status: {status}")
                    return status_data

            except TaskResultError as e:
                if attempt == max_attempts - 1:
                    logger.error(f"❌ Polling timeout after {max_attempts} attempts")
                    raise TaskResultError(f"Polling timeout: {e}")
                logger.debug(f"⏳ Retry {attempt + 1}/{max_attempts} after error")
                time.sleep(self.poll_interval)

        logger.warning(f"⏱️ Polling timeout for task {task_id}, returning partial results")
        return {
            'status': 'timeout',
            'task_id': task_id,
            'error': f'Polling timeout after {max_attempts} attempts',
            'partial': True
        }

    def run_code_audit(
        self,
        project_path: str,
        tools: Optional[List[str]] = None,
        poll: bool = True
    ) -> Dict[str, Any]:
        """
        Convenience wrapper for running code audit tasks.

        Runs linters like pylint, eslint, semgrep on the project.

        Args:
            project_path: Path to project directory
            tools: Optional list of specific tools to run ['pylint', 'eslint', 'semgrep']
            poll: Whether to wait for completion (default: True)

        Returns:
            Dict with audit results

        Raises:
            TaskSubmissionError: If task submission fails
            TaskResultError: If result retrieval fails
        """
        additional_params = {}
        if tools:
            additional_params['tools'] = tools

        logger.info(f"🔍 Running code audit on: {project_path}")

        task_id = self.submit_task(
            project_path=project_path,
            task_type='code_audit',
            additional_params=additional_params
        )

        if poll:
            return self.get_result(task_id, poll=True)
        else:
            return {'task_id': task_id, 'status': 'submitted'}

    def run_security_scan(
        self,
        project_path: str,
        tools: Optional[List[str]] = None,
        poll: bool = True
    ) -> Dict[str, Any]:
        """
        Convenience wrapper for running security scan tasks.

        Runs security tools like bandit, safety on the project.

        Args:
            project_path: Path to project directory
            tools: Optional list of specific tools to run ['bandit', 'safety']
            poll: Whether to wait for completion (default: True)

        Returns:
            Dict with security scan results

        Raises:
            TaskSubmissionError: If task submission fails
            TaskResultError: If result retrieval fails
        """
        additional_params = {}
        if tools:
            additional_params['tools'] = tools

        logger.info(f"🔒 Running security scan on: {project_path}")

        task_id = self.submit_task(
            project_path=project_path,
            task_type='security_scan',
            additional_params=additional_params
        )

        if poll:
            return self.get_result(task_id, poll=True)
        else:
            return {'task_id': task_id, 'status': 'submitted'}

    def submit_custom_task(
        self,
        project_path: str,
        task_definition: Dict[str, Any],
        poll: bool = True
    ) -> Dict[str, Any]:
        """
        Submit a custom task with YAML-based definition.

        Args:
            project_path: Path to project directory
            task_definition: Custom task definition (dict/YAML structure)
            poll: Whether to wait for completion (default: True)

        Returns:
            Dict with task results

        Raises:
            TaskSubmissionError: If task submission fails
            TaskResultError: If result retrieval fails
        """
        logger.info(f"🎯 Submitting custom task for: {project_path}")

        task_id = self.submit_task(
            project_path=project_path,
            task_type='custom',
            additional_params={'definition': task_definition}
        )

        if poll:
            return self.get_result(task_id, poll=True)
        else:
            return {'task_id': task_id, 'status': 'submitted'}

    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()
            logger.info("🔌 Agent Zero Bridge connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


def create_bridge(
    base_url: str = AgentZeroBridge.DEFAULT_BASE_URL,
    timeout: int = AgentZeroBridge.DEFAULT_TIMEOUT
) -> AgentZeroBridge:
    """
    Factory function to create AgentZeroBridge instance.

    Args:
        base_url: Base URL of Agent Zero API
        timeout: Request timeout in seconds

    Returns:
        Configured AgentZeroBridge instance
    """
    return AgentZeroBridge(base_url=base_url, timeout=timeout)

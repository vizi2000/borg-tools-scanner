"""
Unit tests for Agent Zero Bridge module.

Tests HTTP client functionality, error handling, and task submission/retrieval.

Created by The Collective Borg.tools
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import time
from pathlib import Path
import tempfile
import shutil

from agent_zero_bridge import (
    AgentZeroBridge,
    AgentZeroError,
    ConnectionError,
    TaskSubmissionError,
    TaskResultError,
    create_bridge
)


class TestAgentZeroBridge(unittest.TestCase):
    """Test cases for AgentZeroBridge class."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_url = 'http://test.example.com:50001'
        self.bridge = AgentZeroBridge(base_url=self.base_url, timeout=10, poll_interval=1)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        self.bridge.close()
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test bridge initialization."""
        self.assertEqual(self.bridge.base_url, self.base_url)
        self.assertEqual(self.bridge.timeout, 10)
        self.assertEqual(self.bridge.poll_interval, 1)
        self.assertIsNotNone(self.bridge.session)

    def test_initialization_with_defaults(self):
        """Test bridge initialization with default values."""
        bridge = AgentZeroBridge()
        self.assertEqual(bridge.base_url, 'http://borg.tools:50001')
        self.assertEqual(bridge.timeout, 120)
        self.assertEqual(bridge.poll_interval, 5)
        bridge.close()

    @patch('agent_zero_bridge.requests.Session.get')
    def test_health_check_success(self, mock_get):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.json.return_value = {'status': 'healthy', 'version': '1.0'}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.bridge.health_check()

        self.assertEqual(result['status'], 'healthy')
        mock_get.assert_called_once()

    @patch('agent_zero_bridge.requests.Session.get')
    def test_health_check_connection_error(self, mock_get):
        """Test health check with connection error."""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with self.assertRaises(ConnectionError):
            self.bridge.health_check()

    @patch('agent_zero_bridge.requests.Session.post')
    def test_submit_task_success(self, mock_post):
        """Test successful task submission."""
        mock_response = Mock()
        mock_response.json.return_value = {'task_id': 'test-task-123', 'status': 'submitted'}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        task_id = self.bridge.submit_task(self.temp_dir, 'code_audit')

        self.assertEqual(task_id, 'test-task-123')
        mock_post.assert_called_once()

        # Check payload
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        self.assertEqual(payload['task_type'], 'code_audit')
        self.assertIn('project_path', payload)
        self.assertIn('timestamp', payload)

    def test_submit_task_invalid_path(self):
        """Test task submission with invalid project path."""
        with self.assertRaises(TaskSubmissionError):
            self.bridge.submit_task('/nonexistent/path', 'code_audit')

    @patch('agent_zero_bridge.requests.Session.post')
    def test_submit_task_timeout(self, mock_post):
        """Test task submission timeout."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        with self.assertRaises(TaskSubmissionError):
            self.bridge.submit_task(self.temp_dir, 'code_audit')

    @patch('agent_zero_bridge.requests.Session.post')
    def test_submit_task_no_task_id(self, mock_post):
        """Test task submission with missing task_id in response."""
        mock_response = Mock()
        mock_response.json.return_value = {'status': 'submitted'}  # No task_id
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with self.assertRaises(TaskSubmissionError):
            self.bridge.submit_task(self.temp_dir, 'code_audit')

    @patch('agent_zero_bridge.requests.Session.get')
    def test_get_task_status_success(self, mock_get):
        """Test successful task status retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'task_id': 'test-123',
            'status': 'completed',
            'result': {'findings': []}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.bridge.get_task_status('test-123')

        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['task_id'], 'test-123')

    @patch('agent_zero_bridge.requests.Session.get')
    def test_get_task_status_error(self, mock_get):
        """Test task status retrieval with error."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Request failed")

        with self.assertRaises(TaskResultError):
            self.bridge.get_task_status('test-123')

    @patch('agent_zero_bridge.requests.Session.get')
    def test_get_result_no_polling(self, mock_get):
        """Test get_result without polling."""
        mock_response = Mock()
        mock_response.json.return_value = {'task_id': 'test-123', 'status': 'running'}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.bridge.get_result('test-123', poll=False)

        self.assertEqual(result['status'], 'running')
        mock_get.assert_called_once()

    @patch('agent_zero_bridge.requests.Session.get')
    def test_get_result_with_polling_completed(self, mock_get):
        """Test get_result with polling until completion."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'task_id': 'test-123',
            'status': 'completed',
            'result': {'findings': []}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.bridge.get_result('test-123', poll=True)

        self.assertEqual(result['status'], 'completed')

    @patch('agent_zero_bridge.requests.Session.get')
    def test_get_result_with_polling_pending_then_completed(self, mock_get):
        """Test get_result with polling through pending to completed."""
        # First call returns pending, second returns completed
        mock_response_pending = Mock()
        mock_response_pending.json.return_value = {'task_id': 'test-123', 'status': 'pending'}
        mock_response_pending.raise_for_status = Mock()

        mock_response_completed = Mock()
        mock_response_completed.json.return_value = {
            'task_id': 'test-123',
            'status': 'completed',
            'result': {'findings': []}
        }
        mock_response_completed.raise_for_status = Mock()

        mock_get.side_effect = [mock_response_pending, mock_response_completed]

        result = self.bridge.get_result('test-123', poll=True)

        self.assertEqual(result['status'], 'completed')
        self.assertEqual(mock_get.call_count, 2)

    @patch('agent_zero_bridge.requests.Session.get')
    def test_get_result_with_polling_failed(self, mock_get):
        """Test get_result with polling when task fails."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'task_id': 'test-123',
            'status': 'failed',
            'error': 'Something went wrong'
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.bridge.get_result('test-123', poll=True)

        self.assertEqual(result['status'], 'failed')
        self.assertIn('error', result)

    @patch('agent_zero_bridge.requests.Session.get')
    def test_get_result_timeout(self, mock_get):
        """Test get_result with polling timeout."""
        mock_response = Mock()
        mock_response.json.return_value = {'task_id': 'test-123', 'status': 'running'}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.bridge.get_result('test-123', poll=True, max_attempts=2)

        self.assertEqual(result['status'], 'timeout')
        self.assertTrue(result.get('partial', False))

    @patch('agent_zero_bridge.requests.Session.post')
    @patch('agent_zero_bridge.requests.Session.get')
    def test_run_code_audit_success(self, mock_get, mock_post):
        """Test run_code_audit convenience method."""
        # Mock task submission
        mock_post_response = Mock()
        mock_post_response.json.return_value = {'task_id': 'audit-123', 'status': 'submitted'}
        mock_post_response.raise_for_status = Mock()
        mock_post.return_value = mock_post_response

        # Mock task result
        mock_get_response = Mock()
        mock_get_response.json.return_value = {
            'task_id': 'audit-123',
            'status': 'completed',
            'result': {'linters': ['pylint', 'eslint'], 'findings': []}
        }
        mock_get_response.raise_for_status = Mock()
        mock_get.return_value = mock_get_response

        result = self.bridge.run_code_audit(self.temp_dir, tools=['pylint', 'eslint'])

        self.assertEqual(result['status'], 'completed')
        self.assertIn('result', result)

        # Check that tools were passed
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        self.assertEqual(payload['tools'], ['pylint', 'eslint'])

    @patch('agent_zero_bridge.requests.Session.post')
    def test_run_code_audit_no_polling(self, mock_post):
        """Test run_code_audit without polling."""
        mock_response = Mock()
        mock_response.json.return_value = {'task_id': 'audit-123', 'status': 'submitted'}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = self.bridge.run_code_audit(self.temp_dir, poll=False)

        self.assertEqual(result['status'], 'submitted')
        self.assertEqual(result['task_id'], 'audit-123')

    @patch('agent_zero_bridge.requests.Session.post')
    @patch('agent_zero_bridge.requests.Session.get')
    def test_run_security_scan_success(self, mock_get, mock_post):
        """Test run_security_scan convenience method."""
        # Mock task submission
        mock_post_response = Mock()
        mock_post_response.json.return_value = {'task_id': 'scan-123', 'status': 'submitted'}
        mock_post_response.raise_for_status = Mock()
        mock_post.return_value = mock_post_response

        # Mock task result
        mock_get_response = Mock()
        mock_get_response.json.return_value = {
            'task_id': 'scan-123',
            'status': 'completed',
            'result': {'tools': ['bandit', 'safety'], 'vulnerabilities': []}
        }
        mock_get_response.raise_for_status = Mock()
        mock_get.return_value = mock_get_response

        result = self.bridge.run_security_scan(self.temp_dir, tools=['bandit', 'safety'])

        self.assertEqual(result['status'], 'completed')
        self.assertIn('result', result)

    @patch('agent_zero_bridge.requests.Session.post')
    @patch('agent_zero_bridge.requests.Session.get')
    def test_submit_custom_task(self, mock_get, mock_post):
        """Test submit_custom_task method."""
        # Mock task submission
        mock_post_response = Mock()
        mock_post_response.json.return_value = {'task_id': 'custom-123', 'status': 'submitted'}
        mock_post_response.raise_for_status = Mock()
        mock_post.return_value = mock_post_response

        # Mock task result
        mock_get_response = Mock()
        mock_get_response.json.return_value = {
            'task_id': 'custom-123',
            'status': 'completed',
            'result': {'custom_data': 'test'}
        }
        mock_get_response.raise_for_status = Mock()
        mock_get.return_value = mock_get_response

        task_def = {'command': 'pytest', 'args': ['--verbose']}
        result = self.bridge.submit_custom_task(self.temp_dir, task_def)

        self.assertEqual(result['status'], 'completed')

        # Check that definition was passed
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        self.assertEqual(payload['definition'], task_def)

    def test_context_manager(self):
        """Test bridge as context manager."""
        with AgentZeroBridge(base_url=self.base_url) as bridge:
            self.assertIsNotNone(bridge.session)
        # Session should be closed after context exit

    def test_create_bridge_factory(self):
        """Test create_bridge factory function."""
        bridge = create_bridge(base_url='http://custom.url:8080', timeout=60)
        self.assertEqual(bridge.base_url, 'http://custom.url:8080')
        self.assertEqual(bridge.timeout, 60)
        bridge.close()


class TestAgentZeroBridgeIntegration(unittest.TestCase):
    """Integration tests for Agent Zero Bridge (requires actual Agent Zero instance)."""

    @unittest.skipUnless(
        # Only run if AGENT_ZERO_INTEGRATION_TEST env var is set
        __import__('os').environ.get('AGENT_ZERO_INTEGRATION_TEST') == '1',
        "Integration tests disabled (set AGENT_ZERO_INTEGRATION_TEST=1 to enable)"
    )
    def test_health_check_real(self):
        """Test health check against real Agent Zero instance."""
        bridge = AgentZeroBridge()
        try:
            result = bridge.health_check()
            self.assertIsInstance(result, dict)
            print(f"Health check result: {result}")
        except ConnectionError as e:
            self.skipTest(f"Agent Zero not available: {e}")
        finally:
            bridge.close()

    @unittest.skipUnless(
        __import__('os').environ.get('AGENT_ZERO_INTEGRATION_TEST') == '1',
        "Integration tests disabled"
    )
    def test_submit_task_real(self):
        """Test task submission against real Agent Zero instance."""
        bridge = AgentZeroBridge()
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a simple Python file for testing
            test_file = Path(temp_dir) / 'test.py'
            test_file.write_text('print("Hello, World!")\n')

            result = bridge.run_code_audit(temp_dir, poll=False)
            self.assertIn('task_id', result)
            print(f"Task submission result: {result}")
        except (TaskSubmissionError, ConnectionError) as e:
            self.skipTest(f"Agent Zero not available: {e}")
        finally:
            bridge.close()
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)


def run_tests():
    """Run all tests."""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run_tests()

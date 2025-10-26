# Agent Zero Bridge

HTTP client for Agent Zero running on borg.tools:50001. Provides seamless integration for submitting code analysis tasks and retrieving results.

**Created by The Collective Borg.tools**

## Overview

Agent Zero Bridge is a robust HTTP client that connects to Agent Zero agent for automated code audits, security scans, and custom task execution. It handles connection management, task submission, result polling, and graceful error handling.

## Features

- **Connection Management**: Automatic health checks and connection verification
- **Task Submission**: Submit code audits, security scans, and custom tasks
- **Result Polling**: Configurable polling with timeout handling
- **Error Handling**: Graceful fallbacks for connection failures and timeouts
- **Context Manager**: Clean resource management with context manager support
- **Type Safety**: Full type hints for better IDE support
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Installation

The module requires `requests`:

```bash
pip install requests
```

## Quick Start

### 1. Basic Connection Test

```python
from modules.agent_zero_bridge import AgentZeroBridge

# Create bridge and test connection
bridge = AgentZeroBridge()
try:
    health = bridge.health_check()
    print(f"Agent Zero is healthy: {health}")
finally:
    bridge.close()
```

### 2. Run Code Audit

```python
from modules.agent_zero_bridge import AgentZeroBridge

# Use context manager for automatic cleanup
with AgentZeroBridge() as bridge:
    result = bridge.run_code_audit(
        project_path='/path/to/project',
        tools=['pylint', 'eslint'],
        poll=True  # Wait for completion
    )

    if result['status'] == 'completed':
        print(f"Audit complete: {result['result']}")
```

### 3. Run Security Scan

```python
with AgentZeroBridge() as bridge:
    result = bridge.run_security_scan(
        project_path='/path/to/project',
        tools=['bandit', 'safety'],
        poll=True
    )

    print(f"Security scan: {result}")
```

### 4. Submit Custom Task

```python
with AgentZeroBridge() as bridge:
    custom_task = {
        'command': 'pytest',
        'args': ['--verbose', '--cov'],
        'timeout': 300
    }

    result = bridge.submit_custom_task(
        project_path='/path/to/project',
        task_definition=custom_task,
        poll=True
    )
```

## API Reference

### AgentZeroBridge Class

```python
class AgentZeroBridge:
    def __init__(
        self,
        base_url: str = 'http://borg.tools:50001',
        timeout: int = 120,
        poll_interval: int = 5
    )
```

**Parameters:**
- `base_url`: Agent Zero API base URL (default: http://borg.tools:50001)
- `timeout`: Request timeout in seconds (default: 120)
- `poll_interval`: Polling interval in seconds (default: 5)

### Methods

#### health_check()

Test connection to Agent Zero.

```python
def health_check(self) -> Dict[str, Any]:
    """
    Returns:
        Dict with health status information

    Raises:
        ConnectionError: If connection fails
    """
```

**Example:**
```python
bridge = AgentZeroBridge()
health = bridge.health_check()
print(health)  # {'status': 'healthy', 'version': '1.0'}
```

#### submit_task()

Submit a task to Agent Zero.

```python
def submit_task(
    self,
    project_path: str,
    task_type: str,
    additional_params: Optional[Dict[str, Any]] = None
) -> str:
    """
    Args:
        project_path: Absolute path to project directory
        task_type: 'code_audit', 'security_scan', or 'custom'
        additional_params: Optional parameters for the task

    Returns:
        Task ID string

    Raises:
        TaskSubmissionError: If submission fails
    """
```

**Example:**
```python
task_id = bridge.submit_task(
    project_path='/path/to/project',
    task_type='code_audit',
    additional_params={'tools': ['pylint', 'eslint']}
)
print(f"Task submitted: {task_id}")
```

#### get_task_status()

Get current status of a task.

```python
def get_task_status(self, task_id: str) -> Dict[str, Any]:
    """
    Args:
        task_id: Task ID to check

    Returns:
        Dict with task status information

    Raises:
        TaskResultError: If status check fails
    """
```

**Example:**
```python
status = bridge.get_task_status('task-123')
print(f"Status: {status['status']}")  # 'pending', 'running', 'completed', 'failed'
```

#### get_result()

Get result of a submitted task with optional polling.

```python
def get_result(
    self,
    task_id: str,
    poll: bool = True,
    max_attempts: Optional[int] = None
) -> Dict[str, Any]:
    """
    Args:
        task_id: Task ID to retrieve
        poll: Whether to poll until completion (default: True)
        max_attempts: Max polling attempts (default: 60)

    Returns:
        Dict with task results and metadata

    Raises:
        TaskResultError: If retrieval fails or times out
    """
```

**Example:**
```python
# With polling (wait for completion)
result = bridge.get_result('task-123', poll=True)

# Without polling (immediate status)
result = bridge.get_result('task-123', poll=False)

# Custom polling limit
result = bridge.get_result('task-123', poll=True, max_attempts=10)
```

#### run_code_audit()

Convenience wrapper for code audit tasks.

```python
def run_code_audit(
    self,
    project_path: str,
    tools: Optional[List[str]] = None,
    poll: bool = True
) -> Dict[str, Any]:
    """
    Args:
        project_path: Path to project directory
        tools: Optional list ['pylint', 'eslint', 'semgrep']
        poll: Whether to wait for completion

    Returns:
        Dict with audit results
    """
```

**Example:**
```python
# Run all default linters
result = bridge.run_code_audit('/path/to/project')

# Run specific linters
result = bridge.run_code_audit(
    '/path/to/project',
    tools=['pylint', 'eslint']
)

# Submit without waiting
result = bridge.run_code_audit('/path/to/project', poll=False)
print(f"Task ID: {result['task_id']}")
```

#### run_security_scan()

Convenience wrapper for security scan tasks.

```python
def run_security_scan(
    self,
    project_path: str,
    tools: Optional[List[str]] = None,
    poll: bool = True
) -> Dict[str, Any]:
    """
    Args:
        project_path: Path to project directory
        tools: Optional list ['bandit', 'safety']
        poll: Whether to wait for completion

    Returns:
        Dict with security scan results
    """
```

**Example:**
```python
# Run all security tools
result = bridge.run_security_scan('/path/to/project')

# Run specific tools
result = bridge.run_security_scan(
    '/path/to/project',
    tools=['bandit', 'safety']
)
```

#### submit_custom_task()

Submit a custom task with YAML-based definition.

```python
def submit_custom_task(
    self,
    project_path: str,
    task_definition: Dict[str, Any],
    poll: bool = True
) -> Dict[str, Any]:
    """
    Args:
        project_path: Path to project directory
        task_definition: Custom task definition
        poll: Whether to wait for completion

    Returns:
        Dict with task results
    """
```

**Example:**
```python
custom_task = {
    'name': 'run_tests',
    'command': 'pytest',
    'args': ['--verbose', '--cov=.'],
    'timeout': 300,
    'env': {'PYTHONPATH': '/path/to/project'}
}

result = bridge.submit_custom_task(
    '/path/to/project',
    task_definition=custom_task
)
```

### Factory Function

```python
def create_bridge(
    base_url: str = 'http://borg.tools:50001',
    timeout: int = 120
) -> AgentZeroBridge:
    """Create configured AgentZeroBridge instance."""
```

**Example:**
```python
from modules.agent_zero_bridge import create_bridge

bridge = create_bridge(
    base_url='http://custom.url:8080',
    timeout=60
)
```

## Exception Hierarchy

```
AgentZeroError (base exception)
├── ConnectionError (connection failures)
├── TaskSubmissionError (task submission failures)
└── TaskResultError (result retrieval failures)
```

### Error Handling

```python
from modules.agent_zero_bridge import (
    AgentZeroBridge,
    ConnectionError,
    TaskSubmissionError,
    TaskResultError
)

try:
    with AgentZeroBridge() as bridge:
        result = bridge.run_code_audit('/path/to/project')
except ConnectionError as e:
    print(f"Cannot connect to Agent Zero: {e}")
    # Handle connection failure (e.g., fallback to local analysis)
except TaskSubmissionError as e:
    print(f"Failed to submit task: {e}")
    # Handle submission failure
except TaskResultError as e:
    print(f"Failed to get results: {e}")
    # Handle result retrieval failure
```

## Task Types

### 1. Code Audit

Runs linters and static analysis tools.

**Available Tools:**
- `pylint`: Python linter
- `eslint`: JavaScript/TypeScript linter
- `semgrep`: Pattern-based code analysis

**Example Response:**
```json
{
    "status": "completed",
    "task_id": "audit-123",
    "result": {
        "findings": [
            {
                "tool": "pylint",
                "severity": "warning",
                "message": "Line too long",
                "file": "module.py",
                "line": 42
            }
        ],
        "summary": {
            "total_issues": 5,
            "by_severity": {
                "error": 1,
                "warning": 4
            }
        }
    }
}
```

### 2. Security Scan

Runs security analysis tools.

**Available Tools:**
- `bandit`: Python security scanner
- `safety`: Python dependency vulnerability scanner

**Example Response:**
```json
{
    "status": "completed",
    "task_id": "scan-123",
    "result": {
        "vulnerabilities": [
            {
                "tool": "bandit",
                "severity": "high",
                "message": "Use of insecure function",
                "file": "auth.py",
                "line": 15
            }
        ],
        "summary": {
            "total_vulnerabilities": 2,
            "by_severity": {
                "high": 1,
                "medium": 1
            }
        }
    }
}
```

### 3. Custom Task

Run arbitrary commands with custom configuration.

**Task Definition Schema:**
```python
{
    'name': str,              # Task name
    'command': str,           # Command to execute
    'args': List[str],        # Command arguments
    'timeout': int,           # Timeout in seconds
    'env': Dict[str, str],    # Environment variables
    'working_dir': str        # Working directory (optional)
}
```

## Configuration

### Environment Variables

```bash
# Override default Agent Zero URL
export AGENT_ZERO_URL="http://custom.url:50001"

# Set default timeout
export AGENT_ZERO_TIMEOUT="180"

# Enable integration tests
export AGENT_ZERO_INTEGRATION_TEST="1"
```

### Logging Configuration

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or configure specific logger
logger = logging.getLogger('agent_zero_bridge')
logger.setLevel(logging.DEBUG)
```

## Testing

### Run Unit Tests

```bash
# Run all tests
python modules/test_agent_zero_bridge.py

# Run with verbose output
python modules/test_agent_zero_bridge.py -v

# Run specific test
python -m unittest modules.test_agent_zero_bridge.TestAgentZeroBridge.test_health_check_success
```

### Run Integration Tests

```bash
# Enable integration tests (requires Agent Zero running)
export AGENT_ZERO_INTEGRATION_TEST=1
python modules/test_agent_zero_bridge.py
```

### Run Examples

```bash
# Quick connection test
python modules/agent_zero_bridge_example.py test

# Health check example
python modules/agent_zero_bridge_example.py health

# Code audit example
python modules/agent_zero_bridge_example.py audit

# Security scan example
python modules/agent_zero_bridge_example.py security

# Custom task example
python modules/agent_zero_bridge_example.py custom

# Run all examples
python modules/agent_zero_bridge_example.py all
```

## Advanced Usage

### Custom Polling Strategy

```python
bridge = AgentZeroBridge(poll_interval=2)  # Poll every 2 seconds

result = bridge.get_result(
    task_id='task-123',
    poll=True,
    max_attempts=30  # Max 30 attempts = 60 seconds
)
```

### Async Task Submission

```python
# Submit multiple tasks without waiting
task_ids = []
with AgentZeroBridge() as bridge:
    for project in projects:
        task_id = bridge.submit_task(project, 'code_audit')
        task_ids.append(task_id)

    # Poll all tasks later
    results = []
    for task_id in task_ids:
        result = bridge.get_result(task_id, poll=True)
        results.append(result)
```

### Timeout Handling

```python
with AgentZeroBridge(timeout=60) as bridge:
    try:
        result = bridge.run_code_audit(
            '/path/to/project',
            poll=True,
            max_attempts=10  # 50 seconds max
        )

        if result['status'] == 'timeout':
            print("Task is taking longer than expected")
            task_id = result['task_id']
            # Poll again later with more time
            result = bridge.get_result(task_id, poll=True)

    except TaskResultError as e:
        print(f"Task failed: {e}")
```

### Pipeline Integration

```python
def analyze_project(project_path: str) -> Dict[str, Any]:
    """Analyze project with both code audit and security scan."""
    with AgentZeroBridge() as bridge:
        # Run code audit
        audit_result = bridge.run_code_audit(project_path, poll=True)

        # Run security scan
        security_result = bridge.run_security_scan(project_path, poll=True)

        return {
            'audit': audit_result,
            'security': security_result,
            'combined_score': calculate_score(audit_result, security_result)
        }
```

## Performance Considerations

### Connection Pooling

The bridge uses `requests.Session` for automatic connection pooling and keep-alive:

```python
# Single session is reused for all requests
bridge = AgentZeroBridge()
for project in projects:
    bridge.run_code_audit(project)  # Reuses connection
bridge.close()
```

### Polling Efficiency

Default polling parameters are optimized for typical task durations:

- Poll interval: 5 seconds
- Max attempts: 60 (5 minutes total)
- Request timeout: 120 seconds

Adjust based on your task characteristics:

```python
# For quick tasks (< 30 seconds)
bridge = AgentZeroBridge(poll_interval=2)
result = bridge.get_result(task_id, max_attempts=15)

# For long-running tasks (> 10 minutes)
bridge = AgentZeroBridge(poll_interval=10)
result = bridge.get_result(task_id, max_attempts=120)
```

## Troubleshooting

### Connection Errors

**Problem:** `ConnectionError: Failed to connect to Agent Zero`

**Solutions:**
1. Verify Agent Zero is running: `curl http://borg.tools:50001/health`
2. Check network connectivity to borg.tools
3. Test via SSH: `ssh vizi@borg.tools 'curl localhost:50001/health'`
4. Check firewall settings

### Timeout Errors

**Problem:** Tasks timing out during polling

**Solutions:**
1. Increase `max_attempts`: `bridge.get_result(task_id, max_attempts=120)`
2. Increase `poll_interval`: `AgentZeroBridge(poll_interval=10)`
3. Submit without polling and check later: `bridge.run_code_audit(path, poll=False)`

### Invalid Path Errors

**Problem:** `TaskSubmissionError: Project path does not exist`

**Solutions:**
1. Use absolute paths: `Path('/path/to/project').absolute()`
2. Verify path exists: `Path('/path/to/project').exists()`
3. Check permissions: `Path('/path/to/project').is_dir()`

## Integration with Borg.tools Scanner

The Agent Zero Bridge integrates seamlessly with the Borg.tools Scanner pipeline:

```python
from modules import AgentZeroBridge, DocumentationAnalyzer

# Analyze documentation
doc_analyzer = DocumentationAnalyzer()
doc_result = doc_analyzer.analyze('/path/to/project')

# Run code audit via Agent Zero
with AgentZeroBridge() as bridge:
    audit_result = bridge.run_code_audit('/path/to/project')

# Combine results
combined_analysis = {
    'documentation': doc_result,
    'code_quality': audit_result,
    'timestamp': time.time()
}
```

## SSH Access to Agent Zero

You can interact with Agent Zero directly via SSH:

```bash
# Passwordless SSH access
ssh vizi@borg.tools

# Check Agent Zero status
ssh vizi@borg.tools 'curl localhost:50001/health'

# View Agent Zero logs
ssh vizi@borg.tools 'docker logs agent-zero'

# Check running tasks
ssh vizi@borg.tools 'curl localhost:50001/api/tasks'
```

## API Endpoints

### Health Check
- **Endpoint:** `GET /health`
- **Response:** `{'status': 'healthy', 'version': '1.0'}`

### Submit Task
- **Endpoint:** `POST /api/task`
- **Payload:**
  ```json
  {
      "project_path": "/path/to/project",
      "task_type": "code_audit",
      "tools": ["pylint", "eslint"],
      "timestamp": 1698765432.123
  }
  ```
- **Response:** `{'task_id': 'task-123', 'status': 'submitted'}`

### Get Task Status
- **Endpoint:** `GET /api/task/{task_id}`
- **Response:**
  ```json
  {
      "task_id": "task-123",
      "status": "completed",
      "result": {...}
  }
  ```

## Best Practices

1. **Use Context Manager:** Always use `with AgentZeroBridge() as bridge:` for automatic cleanup
2. **Handle Errors:** Catch specific exceptions (`ConnectionError`, `TaskSubmissionError`, `TaskResultError`)
3. **Validate Paths:** Use `Path().absolute()` and verify path exists before submission
4. **Configure Logging:** Enable logging for debugging and monitoring
5. **Tune Polling:** Adjust `poll_interval` and `max_attempts` based on task duration
6. **Connection Pooling:** Reuse bridge instance for multiple tasks
7. **Graceful Degradation:** Handle connection failures with fallback options

## Contributing

When adding new features to Agent Zero Bridge:

1. Add tests to `test_agent_zero_bridge.py`
2. Update this README with examples
3. Add type hints for all parameters
4. Include logging statements for debugging
5. Update the examples script

## License

Created by The Collective Borg.tools

## Support

For issues or questions:
- Check logs with `logging.DEBUG`
- Test connection: `python modules/agent_zero_bridge_example.py test`
- Run unit tests: `python modules/test_agent_zero_bridge.py`
- Check Agent Zero directly: `ssh vizi@borg.tools 'curl localhost:50001/health'`

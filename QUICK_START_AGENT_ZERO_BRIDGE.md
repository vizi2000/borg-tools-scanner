# Quick Start: Agent Zero Bridge

**Connect to Agent Zero on borg.tools:50001 in 5 minutes**

Created by The Collective Borg.tools

---

## What is Agent Zero Bridge?

HTTP client for submitting code analysis tasks to Agent Zero and retrieving results. Perfect for:
- Code audits (pylint, eslint, semgrep)
- Security scans (bandit, safety)
- Custom task execution

## Installation

No additional dependencies needed if you have `requests`:

```bash
pip install requests
```

## 1-Minute Quick Test

```python
from modules import AgentZeroBridge

# Test connection
with AgentZeroBridge() as bridge:
    health = bridge.health_check()
    print(f"✅ Connected: {health}")
```

Run it:
```bash
python -c "from modules import AgentZeroBridge; print(AgentZeroBridge().health_check())"
```

## 5-Minute Full Example

### Step 1: Import

```python
from modules import AgentZeroBridge
```

### Step 2: Run Code Audit

```python
with AgentZeroBridge() as bridge:
    result = bridge.run_code_audit(
        project_path='/path/to/your/project',
        tools=['pylint', 'eslint'],
        poll=True  # Wait for completion
    )

    if result['status'] == 'completed':
        print(f"✅ Audit complete!")
        print(f"Findings: {result['result']}")
    else:
        print(f"⏱️ Status: {result['status']}")
```

### Step 3: Run Security Scan

```python
with AgentZeroBridge() as bridge:
    result = bridge.run_security_scan(
        project_path='/path/to/your/project',
        tools=['bandit', 'safety'],
        poll=True
    )

    print(f"Security scan: {result}")
```

### Step 4: Submit Custom Task

```python
with AgentZeroBridge() as bridge:
    custom_task = {
        'command': 'pytest',
        'args': ['--verbose', '--cov=.'],
        'timeout': 300
    }

    result = bridge.submit_custom_task(
        project_path='/path/to/your/project',
        task_definition=custom_task,
        poll=True
    )

    print(f"Custom task result: {result}")
```

## Common Patterns

### Pattern 1: Quick Check (No Polling)

```python
# Submit task and get task_id immediately
with AgentZeroBridge() as bridge:
    result = bridge.run_code_audit('/path/to/project', poll=False)
    task_id = result['task_id']
    print(f"Task submitted: {task_id}")

    # Check status later
    status = bridge.get_task_status(task_id)
    print(f"Current status: {status['status']}")
```

### Pattern 2: Batch Analysis

```python
# Analyze multiple projects
projects = ['/project1', '/project2', '/project3']

with AgentZeroBridge() as bridge:
    task_ids = []
    for project in projects:
        result = bridge.run_code_audit(project, poll=False)
        task_ids.append(result['task_id'])

    # Poll all tasks
    results = []
    for task_id in task_ids:
        result = bridge.get_result(task_id, poll=True)
        results.append(result)
```

### Pattern 3: Error Handling

```python
from modules import ConnectionError, TaskSubmissionError

try:
    with AgentZeroBridge() as bridge:
        result = bridge.run_code_audit('/path/to/project')
except ConnectionError:
    print("❌ Cannot connect to Agent Zero")
    # Fallback to local analysis
except TaskSubmissionError as e:
    print(f"❌ Task submission failed: {e}")
```

### Pattern 4: Custom Polling

```python
# Fast polling for quick tasks
bridge = AgentZeroBridge(poll_interval=2)  # Poll every 2 seconds
result = bridge.get_result(task_id, max_attempts=15)  # Max 30 seconds

# Slow polling for long tasks
bridge = AgentZeroBridge(poll_interval=10)  # Poll every 10 seconds
result = bridge.get_result(task_id, max_attempts=120)  # Max 20 minutes
```

## Available Task Types

### 1. Code Audit

```python
bridge.run_code_audit(
    project_path='/path/to/project',
    tools=['pylint', 'eslint', 'semgrep'],  # Optional: specify tools
    poll=True  # Wait for completion
)
```

### 2. Security Scan

```python
bridge.run_security_scan(
    project_path='/path/to/project',
    tools=['bandit', 'safety'],  # Optional: specify tools
    poll=True
)
```

### 3. Custom Task

```python
bridge.submit_custom_task(
    project_path='/path/to/project',
    task_definition={
        'command': 'your-command',
        'args': ['--arg1', '--arg2'],
        'timeout': 300,
        'env': {'VAR': 'value'}
    },
    poll=True
)
```

## Error Types

```python
from modules import (
    AgentZeroError,        # Base exception
    ConnectionError,       # Connection failed
    TaskSubmissionError,   # Submit failed
    TaskResultError        # Result retrieval failed
)
```

## Configuration

```python
# Custom Agent Zero URL
bridge = AgentZeroBridge(
    base_url='http://custom.url:8080',
    timeout=60,            # Request timeout (seconds)
    poll_interval=2        # Poll every 2 seconds
)

# Or use factory function
from modules import create_bridge
bridge = create_bridge(base_url='http://custom.url:8080')
```

## Testing

### Run Unit Tests

```bash
python modules/test_agent_zero_bridge.py
```

### Run Quick Connection Test

```bash
python modules/agent_zero_bridge_example.py test
```

### Run All Examples

```bash
python modules/agent_zero_bridge_example.py all
```

## Command Line Examples

### Test Connection

```bash
python -c "from modules import AgentZeroBridge; print(AgentZeroBridge().health_check())"
```

### Run Code Audit (No Polling)

```bash
python -c "
from modules import AgentZeroBridge
bridge = AgentZeroBridge()
result = bridge.run_code_audit('.', poll=False)
print(f'Task ID: {result[\"task_id\"]}')
bridge.close()
"
```

### Check Task Status

```bash
python -c "
from modules import AgentZeroBridge
bridge = AgentZeroBridge()
status = bridge.get_task_status('task-id-here')
print(status)
bridge.close()
"
```

## API Reference (Quick)

### Methods

| Method | Description | Example |
|--------|-------------|---------|
| `health_check()` | Test connection | `bridge.health_check()` |
| `submit_task()` | Submit generic task | `bridge.submit_task('/path', 'code_audit')` |
| `get_task_status()` | Check task status | `bridge.get_task_status('task-123')` |
| `get_result()` | Get task result | `bridge.get_result('task-123', poll=True)` |
| `run_code_audit()` | Run code audit | `bridge.run_code_audit('/path')` |
| `run_security_scan()` | Run security scan | `bridge.run_security_scan('/path')` |
| `submit_custom_task()` | Submit custom task | `bridge.submit_custom_task('/path', {...})` |

### Status Values

- `submitted` - Task submitted, not started
- `pending` - Task queued
- `running` / `in_progress` - Task executing
- `completed` - Task finished successfully
- `failed` - Task failed with error
- `timeout` - Polling timeout (partial result)

## SSH Access to Agent Zero

```bash
# Passwordless SSH
ssh vizi@borg.tools

# Check health
ssh vizi@borg.tools 'curl localhost:50001/health'

# View logs
ssh vizi@borg.tools 'docker logs agent-zero'
```

## Troubleshooting

### Problem: Connection Error

**Solution:**
```bash
# Test connection
curl http://borg.tools:50001/health

# Or via SSH
ssh vizi@borg.tools 'curl localhost:50001/health'
```

### Problem: Timeout

**Solution:**
```python
# Increase polling attempts
result = bridge.get_result(task_id, max_attempts=120)

# Or submit without polling
result = bridge.run_code_audit('/path', poll=False)
# Check later
result = bridge.get_result(task_id)
```

### Problem: Invalid Path

**Solution:**
```python
from pathlib import Path

# Use absolute path
project_path = Path('/path/to/project').absolute()
if project_path.exists():
    result = bridge.run_code_audit(str(project_path))
```

## Integration with Scanner Pipeline

```python
from modules import AgentZeroBridge, DocumentationAnalyzer

# Combine local and remote analysis
doc_analyzer = DocumentationAnalyzer()
doc_result = doc_analyzer.analyze('/path/to/project')

with AgentZeroBridge() as bridge:
    audit_result = bridge.run_code_audit('/path/to/project')

combined = {
    'documentation': doc_result,
    'code_audit': audit_result
}
```

## Tips & Best Practices

1. **Always use context manager** (`with AgentZeroBridge() as bridge:`)
2. **Handle errors** (catch `ConnectionError`, `TaskSubmissionError`, `TaskResultError`)
3. **Use absolute paths** (`Path().absolute()`)
4. **Validate paths** (check `path.exists()` before submission)
5. **Reuse bridge instance** (for multiple tasks)
6. **Configure polling** (adjust `poll_interval` and `max_attempts`)
7. **Enable logging** (for debugging)

## Example: Complete Analysis Script

```python
#!/usr/bin/env python3
"""Analyze project with Agent Zero"""

from modules import AgentZeroBridge, ConnectionError
import sys

def analyze_project(project_path: str):
    try:
        with AgentZeroBridge() as bridge:
            # Run code audit
            print("Running code audit...")
            audit = bridge.run_code_audit(project_path, poll=True)

            # Run security scan
            print("Running security scan...")
            security = bridge.run_security_scan(project_path, poll=True)

            # Print results
            print("\n=== RESULTS ===")
            print(f"Audit: {audit['status']}")
            print(f"Security: {security['status']}")

            return {'audit': audit, 'security': security}

    except ConnectionError:
        print("❌ Cannot connect to Agent Zero")
        return None

if __name__ == '__main__':
    project = sys.argv[1] if len(sys.argv) > 1 else '.'
    analyze_project(project)
```

Save as `analyze.py` and run:

```bash
python analyze.py /path/to/project
```

## More Information

- **Full Documentation:** `/Users/wojciechwiesner/ai/_Borg.tools_scan/modules/README_AGENT_ZERO_BRIDGE.md`
- **Examples:** `/Users/wojciechwiesner/ai/_Borg.tools_scan/modules/agent_zero_bridge_example.py`
- **Tests:** `/Users/wojciechwiesner/ai/_Borg.tools_scan/modules/test_agent_zero_bridge.py`
- **Completion Report:** `/Users/wojciechwiesner/ai/_Borg.tools_scan/TASK_4A_COMPLETION_REPORT.md`

## Support

- Test connection: `python modules/agent_zero_bridge_example.py test`
- Run examples: `python modules/agent_zero_bridge_example.py all`
- Check Agent Zero: `ssh vizi@borg.tools 'curl localhost:50001/health'`

---

**Happy Analyzing! 🚀**

Created by The Collective Borg.tools

# Task 4A: Agent Zero Bridge

## Objective
HTTP client komunikujący z Agent Zero na borg.tools:50001.

## Priority: 🟢 MEDIUM | Time: 4h | Dependencies: None

## Agent Zero Details
- URL: http://borg.tools:50001
- SSH: ssh vizi@borg.tools (passwordless)
- Running in Docker on borg.tools

## Output
```python
# agent_zero_bridge.py
class AgentZeroBridge:
    def submit_task(project_path: str, task_type: str) -> str:
        # Returns task_id
    def get_result(task_id: str) -> Dict:
        # Poll for completion
    def run_code_audit(project_path: str) -> Dict:
        # Convenience wrapper
```

## Communication Protocol
- HTTP POST /api/task with JSON payload
- Poll GET /api/task/{id} for status
- Parse result JSON

## Test
```bash
# Verify connection
curl http://borg.tools:50001/health
# Submit test task
python -c "from agent_zero_bridge import AgentZeroBridge; print(AgentZeroBridge().submit_task('/tmp/test', 'audit'))"
```

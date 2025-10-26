# Task 4B: Autonomous Code Auditor Workflow

## Objective
A0 task templates dla code quality audits.

## Priority: 🟢 MEDIUM | Time: 4h | Dependencies: Task 4A

## Output
```yaml
# agent_zero_workflows/code_audit.yaml
task:
  type: code_audit
  tools: [pylint, eslint, semgrep, bandit]
  steps:
    - Install linters
    - Run on all files
    - Aggregate results
    - Generate report
```

## Integration
- Bridge submits workflow YAML to A0
- A0 executes autonomously
- Results parsed into CODE_QUALITY_SCORE

## Expected Output from A0
```json
{
  "pylint_score": 7.2,
  "eslint_errors": 15,
  "security_issues": [{"severity": "HIGH", "file": "app.py", ...}],
  "complexity_warnings": 8
}
```

## Test: Run on sample project, verify A0 completes audit in <90s

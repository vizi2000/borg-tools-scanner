# Quick Start: Agent Zero Auditor

**5-minute guide to using the Agent Zero Autonomous Code Auditor**

---

## What is it?

Autonomous code audit system that runs 3 comprehensive checks:
1. **Code Quality** - Linting, formatting, type checking
2. **Security** - Vulnerabilities, secrets, dependencies
3. **Complexity** - Cyclomatic complexity, technical debt, maintainability

**Result**: Bonus +0 to +6 points added to your project score!

---

## Quick Test

```bash
# 1. Run tests (verify everything works)
cd /Users/wojciechwiesner/ai/_Borg.tools_scan
PYTHONPATH=. python3 modules/test_agent_zero_auditor.py

# Expected output:
# ✅ All tests passed!
# Ran 14 tests in 0.002s
```

```bash
# 2. Run integration example
PYTHONPATH=. python3 agent_zero_integration_example.py

# Expected output:
# Without Agent Zero: Value Score = 7
# With Agent Zero:    Value Score = 11
# Improvement: +4 points
```

---

## Files Structure

```
agent_zero_workflows/          # Workflow definitions
├── code_audit.yaml           # Pylint, ESLint, etc.
├── security_scan.yaml        # Bandit, Semgrep, etc.
└── complexity_analysis.yaml  # Radon, Lizard, etc.

modules/
├── agent_zero_auditor.py     # Core module
└── test_agent_zero_auditor.py # Tests

agent_zero_integration_example.py  # Usage example
```

---

## Python API

### Basic Usage

```python
from modules.agent_zero_auditor import AgentZeroAuditor

# Initialize
auditor = AgentZeroAuditor()

# Parse results from Agent Zero
raw_result = {
    "pylint_score": 8.5,
    "pylint_errors": 2,
    "overall_score": 8.2
}

parsed = auditor.parse_agent_zero_audit(raw_result, "code_audit")
print(f"Code Quality: {parsed.code_quality_score}/10")
```

### Full Workflow

```python
from pathlib import Path
from modules.agent_zero_auditor import AgentZeroAuditor

# Run all 3 audits
auditor = AgentZeroAuditor()
project_path = Path(".")

workflows = ["code_audit", "security_scan", "complexity_analysis"]
all_results = []

for workflow in workflows:
    # In production, use Agent Zero Bridge:
    # raw_result = bridge.submit_and_get(project_path, workflow)

    # For testing, use mock data
    raw_result = {...}  # From Agent Zero

    parsed = auditor.parse_agent_zero_audit(raw_result, workflow)
    all_results.append(parsed)

# Aggregate
aggregated = auditor.aggregate_results(all_results)

print(f"Overall Score: {aggregated['overall_score']:.1f}/10")
print(f"Bonus Score: +{aggregated['bonus_score']:.1f}")
print(f"\nRecommendations:")
for rec in aggregated['recommendations']:
    print(f"  - {rec}")
```

---

## Bonus Scoring

| Audit | Score | Bonus |
|-------|-------|-------|
| Code Quality ≥ 9.0 | Excellent | +2.0 |
| Code Quality ≥ 7.0 | Good | +1.0 |
| Security ≥ 9.0 (no secrets) | Excellent | +3.0 |
| Security ≥ 7.0 | Good | +1.5 |
| Complexity ≥ 8.0 | Good | +1.0 |

**Maximum bonus**: 6 points

---

## Integration with Main Scanner

Add to `scan_project()` in `borg_tools_scan.py`:

```python
from modules.agent_zero_auditor import AgentZeroAuditor

def scan_project(p: Path, use_agent_zero: bool = False):
    # ... existing code ...

    if use_agent_zero:
        auditor = AgentZeroAuditor()

        # Run audits (when Agent Zero Bridge is ready)
        # workflows = ["code_audit", "security_scan", "complexity_analysis"]
        # all_results = []
        # for workflow in workflows:
        #     result = run_workflow_via_bridge(p, workflow)
        #     parsed = auditor.parse_agent_zero_audit(result, workflow)
        #     all_results.append(parsed)

        # aggregated = auditor.aggregate_results(all_results)
        # value_score += int(aggregated["bonus_score"])

    return ProjectSummary(...)
```

**CLI**:
```bash
python borg_tools_scan.py --root ~/Projects --use-agent-zero
```

---

## Example Output

### Code Audit
```json
{
  "workflow": "code_audit",
  "code_quality_score": 7.9,
  "pylint_errors": 3,
  "pylint_warnings": 12,
  "overall_score": 7.9
}
```

### Security Scan
```json
{
  "workflow": "security_scan",
  "security_score": 8.2,
  "high_severity": 1,
  "secrets_found": 0,
  "vulnerable_dependencies": 2
}
```

### Complexity Analysis
```json
{
  "workflow": "complexity_analysis",
  "complexity_score": 8.5,
  "avg_cyclomatic_complexity": 8.3,
  "technical_debt_score": 25.4
}
```

### Aggregated
```json
{
  "overall_score": 8.2,
  "bonus_score": 4.0,
  "recommendations": [
    "Fix 1 high-severity security issue immediately",
    "Continue maintaining code quality standards"
  ]
}
```

---

## Workflow Details

### Code Audit
**Time**: ~30 seconds
**Tools**: pylint, flake8, black, mypy, ruff, eslint
**Checks**: Syntax errors, style issues, type errors, unused code

### Security Scan
**Time**: ~45 seconds
**Tools**: bandit, safety, semgrep, npm-audit, secrets scanner
**Checks**: Vulnerabilities, exposed secrets, unsafe patterns, outdated deps

### Complexity Analysis
**Time**: ~15 seconds
**Tools**: radon, lizard, LOC counter
**Checks**: Cyclomatic complexity, function length, technical debt, maintainability

**Total Time**: ~90 seconds for all 3 workflows

---

## Troubleshooting

### Import Error
```bash
# Error: ModuleNotFoundError: No module named 'modules'

# Solution: Set PYTHONPATH
PYTHONPATH=/Users/wojciechwiesner/ai/_Borg.tools_scan python3 script.py
```

### YAML Error
```bash
# Error: yaml.YAMLError

# Solution: Install PyYAML
pip install pyyaml
```

### Missing Workflows
```bash
# Error: Workflow not found

# Solution: Check workflows directory exists
ls -la agent_zero_workflows/
# Should show: code_audit.yaml, security_scan.yaml, complexity_analysis.yaml
```

---

## Next Steps

1. **Task 4A**: Implement Agent Zero Bridge to communicate with borg.tools:50001
2. **Task 5A**: Integrate auditor into main scanner
3. **Testing**: Run on real projects with Agent Zero
4. **Tuning**: Adjust scoring thresholds based on results

---

## Quick Reference

```bash
# Test the auditor
PYTHONPATH=. python3 modules/test_agent_zero_auditor.py

# Run integration example
PYTHONPATH=. python3 agent_zero_integration_example.py

# Demo the module
PYTHONPATH=. python3 modules/agent_zero_auditor.py

# View workflows
cat agent_zero_workflows/code_audit.yaml

# Check test coverage
grep -c "def test_" modules/test_agent_zero_auditor.py
# Output: 14
```

---

## Resources

- **Full Documentation**: `/AGENT_ZERO_AUDITOR_README.md`
- **Completion Report**: `/TASK_4B_COMPLETION_REPORT.md`
- **Integration Example**: `/agent_zero_integration_example.py`
- **Test Suite**: `/modules/test_agent_zero_auditor.py`

---

**Created by The Collective Borg.tools**
**Ready for production use with Agent Zero Bridge**

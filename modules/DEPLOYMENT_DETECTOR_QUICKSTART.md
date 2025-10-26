# Deployment Detector - Quick Start Guide

## 1-Minute Integration

### Installation
```bash
# Install optional dependency for docker-compose support
pip install pyyaml
```

### Basic Usage
```python
from modules.deployment_detector import detect_deployment

# Run deployment analysis
result = detect_deployment(
    project_path="/path/to/project",
    languages=["python"],  # or ["nodejs"], ["python", "nodejs"], etc.
    facts={"deps": {}, "has_ci": False}
)

# Access results
score = result['deployment']['readiness_score']  # 0-10
is_deployable = result['deployment']['is_deployable']  # bool
blockers = result['deployment']['blockers']  # list
mvp_hours = result['deployment']['estimated_hours_to_mvp']  # float
```

### Example Output
```python
{
  "deployment": {
    "readiness_score": 8,          # 0-10 score
    "is_deployable": true,          # ≥7 = deployable
    "deployment_type": "docker",    # docker/unknown
    "target_platform": "borg.tools",# borg.tools/vercel/aws_lambda/etc.
    "blockers": [...],              # List of issues to fix
    "mvp_checklist": [...],         # Tasks with time estimates
    "estimated_hours_to_mvp": 2.5   # Total hours needed
  }
}
```

## Common Use Cases

### 1. Get Deployment Readiness Score
```python
result = detect_deployment(path, langs, facts)
if result['deployment']['is_deployable']:
    print("✅ Ready to deploy!")
else:
    print(f"❌ Score: {result['deployment']['readiness_score']}/10")
```

### 2. List All Blockers
```python
for blocker in result['deployment']['blockers']:
    print(f"[{blocker['severity']}] {blocker['description']}")
    print(f"  Fix: {blocker['suggestion']}")
    print(f"  Time: {blocker['estimated_fix_time_hours']}h\n")
```

### 3. Get Environment Variables
```python
env_vars = result['deployment']['environment_vars']
undocumented = [v for v in env_vars if not v['documented']]
print(f"Found {len(undocumented)} undocumented env vars")
```

### 4. Generate MVP Checklist
```python
checklist = result['deployment']['mvp_checklist']
for task in checklist:
    status = task['status']  # done/blocked/missing/pending
    print(f"[{status}] {task['task']} - {task['time_hours']}h")
```

## Integration with Scanner

```python
def scan_project(project_path):
    # ... existing scan logic ...

    # Add deployment analysis
    deployment = detect_deployment(
        project_path=project_path,
        languages=detected_languages,
        facts={"deps": dependencies, "has_ci": has_ci}
    )

    # Merge into scan results
    scan_results.update(deployment)

    return scan_results
```

## Blocker Severity Levels

- **CRITICAL** 🔴: Blocks deployment (e.g., no Dockerfile)
- **HIGH** ⚠️: Strongly recommended (e.g., undocumented env vars)
- **MEDIUM** 📝: Should fix for production (e.g., no build script)
- **LOW** ℹ️: Nice to have (e.g., no HEALTHCHECK)

## Readiness Score Breakdown

```
10 = Perfect deployment setup
 9 = Production ready, minor improvements possible
 8 = Deployable with some warnings
 7 = Minimum viable deployment (threshold)
 6 = Major issues, needs work
 5 = Multiple critical issues
0-4 = Not ready for deployment
```

## Performance

- **Average**: 0.001-0.016 seconds per project
- **Memory**: <10MB
- **Scalability**: Handles 1000s of files efficiently

## Files Overview

```
modules/
├── deployment_detector.py              - Main module (USE THIS)
├── test_deployment_detector.py         - Test suite
├── deployment_detector_example.py      - Examples
├── README_deployment_detector.md       - Full docs
├── DEPLOYMENT_DETECTOR_SUMMARY.md      - Implementation summary
└── DEPLOYMENT_DETECTOR_QUICKSTART.md   - This file
```

## Common Patterns

### Check if Docker is present
```python
if result['deployment']['detected_artifacts']['dockerfile']:
    print("✅ Dockerfile found")
```

### Get deployment instructions
```python
instructions = result['deployment']['deployment_instructions']
print(instructions)  # Platform-specific guide
```

### Filter blockers by severity
```python
critical = [b for b in blockers if b['severity'] == 'CRITICAL']
high = [b for b in blockers if b['severity'] == 'HIGH']
```

## Troubleshooting

**Q: PyYAML not installed?**
```bash
pip install pyyaml
# Module works without it, but docker-compose parsing is disabled
```

**Q: No environment variables detected?**
- Module scans for `os.getenv()` (Python) and `process.env` (JS)
- Check if your code uses these patterns
- Custom config loaders may not be detected

**Q: Low readiness score?**
- Check `blockers` list for specific issues
- Fix CRITICAL and HIGH severity items first
- Refer to `mvp_checklist` for action items

## Quick Test

```bash
# Run test suite
python3 modules/test_deployment_detector.py

# Run examples
python3 modules/deployment_detector_example.py
```

## Support

- **Docs**: modules/README_deployment_detector.md
- **Examples**: modules/deployment_detector_example.py
- **Tests**: modules/test_deployment_detector.py
- **Created by**: The Collective Borg.tools

---

**Ready to use! 🚀**

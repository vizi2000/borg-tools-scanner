# Deployment Detector Module

Automatic deployment readiness analysis for software projects.

## Overview

The Deployment Detector is a standalone Python module that analyzes projects for deployment readiness, generates actionable blockers, and provides an MVP checklist with time estimates.

## Features

- **Dockerfile Analysis**: Parse and validate Dockerfiles (base images, ports, ENV vars)
- **Docker Compose Support**: Extract service architecture from docker-compose.yml
- **Environment Variable Detection**: Scan code for `os.getenv()`, `process.env` patterns
- **Build Validation**: Detect setup.py, package.json build scripts, Makefiles
- **Platform Inference**: Automatically detect target platform (Docker/Vercel/AWS Lambda)
- **Readiness Scoring**: 0-10 score based on deployment criteria
- **Blocker Identification**: Critical, High, Medium, Low severity with fix time estimates
- **MVP Checklist**: Actionable tasks with status and time estimates

## Installation

```bash
# Required for docker-compose parsing
pip install pyyaml
```

## Usage

### Basic Usage

```python
from deployment_detector import detect_deployment

result = detect_deployment(
    project_path="/path/to/project",
    languages=["python"],
    facts={"deps": {"python": ["flask"]}, "has_ci": False}
)

print(f"Readiness Score: {result['deployment']['readiness_score']}/10")
print(f"Is Deployable: {result['deployment']['is_deployable']}")
print(f"Blockers: {len(result['deployment']['blockers'])}")
```

### Output Format

```json
{
  "deployment": {
    "readiness_score": 8,
    "is_deployable": true,
    "deployment_type": "docker",
    "target_platform": "borg.tools",
    "detected_artifacts": {
      "dockerfile": true,
      "docker_compose": true,
      "requirements_txt": true,
      "package_json": false,
      "env_example": true
    },
    "environment_vars": [
      {"name": "DATABASE_URL", "required": true, "documented": true}
    ],
    "ports": [8080],
    "services": ["web", "db"],
    "build_validation": {
      "has_build_script": true,
      "build_command": "python setup.py build"
    },
    "blockers": [
      {
        "severity": "HIGH",
        "category": "environment",
        "description": "2 undocumented environment variables",
        "estimated_fix_time_hours": 1,
        "suggestion": "Create .env.example with: API_KEY, SECRET_KEY"
      }
    ],
    "mvp_checklist": [
      {"task": "Create Dockerfile", "status": "done", "time_hours": 0},
      {"task": "Document environment variables", "status": "missing", "time_hours": 1}
    ],
    "estimated_hours_to_mvp": 1.0,
    "deployment_instructions": "# Deployment to borg.tools\n..."
  }
}
```

## Components

### 1. DockerfileParser
Extracts:
- Base image (FROM)
- Exposed ports (EXPOSE)
- Environment variables (ENV)
- Validates for deprecated images (python:2.7, :latest tags)

### 2. DockerComposeParser
Extracts:
- Services
- Networks
- Volumes
- Multi-service architecture detection

### 3. EnvironmentDetector
Scans for:
- Python: `os.getenv('VAR')`, `os.environ.get('VAR')`, `os.environ['VAR']`
- JavaScript/TypeScript: `process.env.VAR`
- Cross-references with `.env.example` for documentation status

### 4. BuildValidator
Detects:
- Python: `setup.py`, `pyproject.toml`
- Node.js: `package.json` build scripts
- `Makefile` targets

### 5. PlatformDetector
Infers platform from:
- `vercel.json` → Vercel
- `serverless.yml` → AWS Lambda
- `Dockerfile` → Docker (borg.tools)
- `index.html` + no deps → Static hosting

### 6. DeploymentDetector
Main orchestrator that:
- Runs all parsers
- Identifies blockers (CRITICAL/HIGH/MEDIUM/LOW)
- Computes readiness score (0-10)
- Generates MVP checklist
- Provides deployment instructions

## Readiness Score Calculation

The score (0-10) is based on:
- **+3**: Dockerfile exists
- **+2**: Dockerfile has no issues (valid base image, proper syntax)
- **+2**: All environment variables documented
- **+2**: No critical blockers
- **+1**: No high severity blockers

Score ≥ 7 = deployable ✅

## Blocker Severities

- **CRITICAL**: Blocks deployment (e.g., no Dockerfile)
- **HIGH**: Strongly recommended before deployment (e.g., undocumented env vars)
- **MEDIUM**: Should fix for production (e.g., no build script)
- **LOW**: Nice to have (e.g., no HEALTHCHECK)

## Testing

```bash
# Run comprehensive test suite
python3 modules/test_deployment_detector.py

# Run examples
python3 modules/deployment_detector_example.py
```

## Integration Example

```python
# In your main scanner
from deployment_detector import detect_deployment

def scan_project(project_path, languages):
    # ... other scanning logic ...

    # Add deployment analysis
    deployment_result = detect_deployment(
        project_path=project_path,
        languages=languages,
        facts={"deps": detected_dependencies, "has_ci": has_ci_config}
    )

    # Merge with other scan results
    scan_results.update(deployment_result)

    return scan_results
```

## Performance

- Scans complete in <10 seconds per project
- Handles large codebases efficiently
- Graceful error handling for invalid files

## Edge Cases Handled

- Non-existent files (returns safe defaults)
- Invalid YAML in docker-compose (reports parse error)
- Multiple Dockerfiles (uses root directory)
- Missing dependencies (PyYAML optional, degrades gracefully)
- Invalid project paths (returns low readiness score)

## Files

- `deployment_detector.py` - Main module (600+ lines)
- `test_deployment_detector.py` - Comprehensive test suite
- `deployment_detector_example.py` - Usage examples

## Success Metrics

✅ Detects deployment type accurately
✅ Identifies all environment variables in code
✅ Computes realistic readiness scores
✅ Generates actionable blockers with time estimates
✅ Runs in <10s per project
✅ All tests passing

## Created by

**The Collective Borg.tools**
Task 1B: Deployment Detection System
Part of Borg Tools Scanner v2.0 upgrade

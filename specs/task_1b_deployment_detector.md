# Task 1B: Deployment Detection System

## Objective
Stworzyć moduł `deployment_detector.py` automatycznie wykrywający typ deploymentu projektu, jego gotowość do wdrożenia, oraz generujący szczegółowy checklist blokerów i kroków do MVP.

## Priority
🔴 **CRITICAL** - Foundation dla DEPLOYMENT_READINESS_SCORE

## Estimated Time
3 hours

## Dependencies
**None** - standalone module, działa równolegle z Task 1A i 1C

## Input Format
```python
{
    "project_path": "/path/to/project",
    "languages": ["python", "nodejs"],
    "facts": {
        "has_ci": false,
        "deps": {"python": ["flask", "gunicorn"], "node": []}
    }
}
```

## Output Format
```json
{
    "deployment": {
        "readiness_score": 3,
        "is_deployable": false,
        "deployment_type": "docker",
        "target_platform": "borg.tools",
        "detected_artifacts": {
            "dockerfile": true,
            "docker_compose": false,
            "requirements_txt": true,
            "package_json": false,
            "env_example": false
        },
        "environment_vars": [
            {"name": "DATABASE_URL", "required": true, "documented": false},
            {"name": "API_KEY", "required": true, "documented": false},
            {"name": "PORT", "required": false, "documented": true, "default": "5000"}
        ],
        "ports": [5000, 8080],
        "services": ["web", "postgres"],
        "build_validation": {
            "has_build_script": true,
            "build_command": "python setup.py build",
            "build_success_testable": false
        },
        "blockers": [
            {
                "severity": "CRITICAL",
                "category": "dockerfile",
                "description": "Dockerfile uses deprecated base image (python:2.7)",
                "estimated_fix_time_hours": 2,
                "suggestion": "Update to python:3.11-slim"
            },
            {
                "severity": "HIGH",
                "category": "environment",
                "description": "No .env.example file - 5 undocumented env vars",
                "estimated_fix_time_hours": 1,
                "suggestion": "Create .env.example with: DATABASE_URL, API_KEY, SECRET_KEY, REDIS_URL, PORT"
            }
        ],
        "mvp_checklist": [
            {"task": "Create Dockerfile", "status": "done", "time_hours": 0},
            {"task": "Document environment variables", "status": "blocked", "time_hours": 1},
            {"task": "Add health check endpoint", "status": "missing", "time_hours": 0.5},
            {"task": "Test local deployment", "status": "pending", "time_hours": 1}
        ],
        "estimated_hours_to_mvp": 2.5,
        "deployment_instructions": "# Deployment to borg.tools\n1. Fix Dockerfile base image\n2. Create .env.example\n3. Run: docker build -t project .\n4. Deploy: scp to vizi@borg.tools, docker run"
    }
}
```

## Implementation Details

### 1. Dockerfile Parser
```python
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

class DockerfileParser:
    def parse(self, dockerfile_path: Path) -> Dict[str, Any]:
        """
        Extract:
        - Base image (FROM)
        - Exposed ports (EXPOSE)
        - Environment variables (ENV)
        - Build steps validity
        """
        if not dockerfile_path.exists():
            return {'exists': False}

        content = dockerfile_path.read_text(encoding='utf-8', errors='ignore')

        # Regex patterns
        from_pattern = r'FROM\s+([\w:\./-]+)'
        expose_pattern = r'EXPOSE\s+(\d+)'
        env_pattern = r'ENV\s+(\w+)(?:\s+|=)(.+)'

        base_image = re.search(from_pattern, content)
        ports = re.findall(expose_pattern, content)
        env_vars = re.findall(env_pattern, content)

        # Validation
        issues = []
        if base_image:
            img = base_image.group(1)
            if 'python:2' in img or ':latest' in img:
                issues.append('deprecated_or_unpinned_base_image')

        return {
            'exists': True,
            'base_image': base_image.group(1) if base_image else None,
            'ports': [int(p) for p in ports],
            'env_vars': dict(env_vars),
            'issues': issues
        }
```

### 2. Docker Compose Parser
```python
import yaml

class DockerComposeParser:
    def parse(self, compose_path: Path) -> Dict[str, Any]:
        """
        Extract services, dependencies, networks, volumes
        """
        if not compose_path.exists():
            return {'exists': False}

        try:
            with open(compose_path, 'r') as f:
                compose = yaml.safe_load(f)

            services = list(compose.get('services', {}).keys())
            networks = list(compose.get('networks', {}).keys())
            volumes = list(compose.get('volumes', {}).keys())

            return {
                'exists': True,
                'services': services,
                'networks': networks,
                'volumes': volumes,
                'is_multi_service': len(services) > 1
            }
        except Exception as e:
            return {'exists': True, 'parse_error': str(e)}
```

### 3. Environment Variable Detector
```python
class EnvironmentDetector:
    def detect_env_vars(self, project_path: Path) -> List[Dict]:
        """
        Scan code for os.getenv(), process.env, config.get() patterns
        Check if .env.example exists
        """
        env_vars = set()

        # Python: os.getenv, os.environ.get
        for py_file in project_path.rglob('*.py'):
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            # Pattern: os.getenv('VAR_NAME') or os.environ['VAR_NAME']
            matches = re.findall(r'os\.(?:getenv|environ\.get)\([\'"](\w+)[\'"]', content)
            env_vars.update(matches)

        # JavaScript: process.env.VAR_NAME
        for js_file in project_path.rglob('*.js'):
            content = js_file.read_text(encoding='utf-8', errors='ignore')
            matches = re.findall(r'process\.env\.(\w+)', content)
            env_vars.update(matches)

        # Check documentation
        env_example = project_path / '.env.example'
        documented_vars = set()
        if env_example.exists():
            documented_vars = set(re.findall(r'^(\w+)=', env_example.read_text(), re.MULTILINE))

        return [
            {
                'name': var,
                'required': True,  # heuristic: all detected vars assumed required
                'documented': var in documented_vars
            }
            for var in sorted(env_vars)
        ]
```

### 4. Build Script Validator
```python
class BuildValidator:
    def validate(self, project_path: Path, languages: List[str]) -> Dict[str, Any]:
        """
        Check for build scripts:
        - Python: setup.py, pyproject.toml build config
        - Node: package.json scripts.build
        - Makefile
        """
        results = {'has_build_script': False, 'build_command': None}

        # Python
        if 'python' in languages:
            if (project_path / 'setup.py').exists():
                results['has_build_script'] = True
                results['build_command'] = 'python setup.py build'
            elif (project_path / 'pyproject.toml').exists():
                toml = (project_path / 'pyproject.toml').read_text()
                if '[build-system]' in toml:
                    results['has_build_script'] = True
                    results['build_command'] = 'pip install .'

        # Node
        if 'nodejs' in languages:
            pkg_json = project_path / 'package.json'
            if pkg_json.exists():
                import json
                data = json.loads(pkg_json.read_text())
                if 'build' in data.get('scripts', {}):
                    results['has_build_script'] = True
                    results['build_command'] = 'npm run build'

        # Makefile
        if (project_path / 'Makefile').exists():
            results['has_build_script'] = True
            results['build_command'] = 'make build'

        return results
```

### 5. Platform Inference
```python
class PlatformDetector:
    def infer_platform(self, project_path: Path, deps: Dict) -> str:
        """
        Heuristic detection:
        - vercel.json → Vercel
        - serverless.yml → AWS Lambda
        - Dockerfile → Docker (borg.tools, any Docker host)
        - Static HTML → GitHub Pages / Netlify
        """
        if (project_path / 'vercel.json').exists():
            return 'vercel'
        elif (project_path / 'serverless.yml').exists():
            return 'aws_lambda'
        elif (project_path / 'Dockerfile').exists():
            return 'docker_generic'  # could be borg.tools
        elif (project_path / 'index.html').exists() and not deps:
            return 'static_hosting'
        else:
            return 'unknown'
```

### 6. Main Orchestrator
```python
# deployment_detector.py

from pathlib import Path
from typing import Dict, Any, List

class DeploymentDetector:
    def __init__(self):
        self.dockerfile_parser = DockerfileParser()
        self.compose_parser = DockerComposeParser()
        self.env_detector = EnvironmentDetector()
        self.build_validator = BuildValidator()
        self.platform_detector = PlatformDetector()

    def analyze(self, project_path: Path, languages: List[str], facts: Dict) -> Dict[str, Any]:
        """Main entry point"""
        print(f"🚀 [DEPLOYMENT DETECTOR] Analyzing {project_path.name}...")

        # Parse artifacts
        dockerfile = self.dockerfile_parser.parse(project_path / 'Dockerfile')
        compose = self.compose_parser.parse(project_path / 'docker-compose.yml')
        env_vars = self.env_detector.detect_env_vars(project_path)
        build_info = self.build_validator.validate(project_path, languages)
        platform = self.platform_detector.infer_platform(project_path, facts.get('deps', {}))

        # Detect blockers
        blockers = self._identify_blockers(dockerfile, compose, env_vars, build_info)

        # Compute score
        score = self._compute_readiness_score(dockerfile, env_vars, blockers)

        # Generate checklist
        checklist = self._generate_mvp_checklist(blockers, dockerfile, env_vars)

        print(f"  📊 Deployment Readiness: {score}/10")
        print(f"  🔴 Blockers: {len([b for b in blockers if b['severity'] in ['CRITICAL', 'HIGH']])}")

        return {
            'deployment': {
                'readiness_score': score,
                'is_deployable': score >= 7,
                'deployment_type': 'docker' if dockerfile['exists'] else 'unknown',
                'target_platform': platform,
                'detected_artifacts': {
                    'dockerfile': dockerfile['exists'],
                    'docker_compose': compose['exists'],
                    'env_example': (project_path / '.env.example').exists()
                },
                'environment_vars': env_vars,
                'ports': dockerfile.get('ports', []),
                'services': compose.get('services', []),
                'build_validation': build_info,
                'blockers': blockers,
                'mvp_checklist': checklist,
                'estimated_hours_to_mvp': sum(item['time_hours'] for item in checklist if item['status'] != 'done'),
                'deployment_instructions': self._generate_instructions(platform, dockerfile)
            }
        }

    def _identify_blockers(self, dockerfile, compose, env_vars, build_info) -> List[Dict]:
        """Identify deployment blockers"""
        blockers = []

        # Dockerfile issues
        if not dockerfile['exists']:
            blockers.append({
                'severity': 'CRITICAL',
                'category': 'dockerfile',
                'description': 'No Dockerfile found',
                'estimated_fix_time_hours': 2,
                'suggestion': 'Create Dockerfile with appropriate base image and COPY/RUN steps'
            })
        elif 'deprecated_or_unpinned_base_image' in dockerfile.get('issues', []):
            blockers.append({
                'severity': 'HIGH',
                'category': 'dockerfile',
                'description': 'Dockerfile uses deprecated/unpinned base image',
                'estimated_fix_time_hours': 0.5,
                'suggestion': 'Pin to specific version (e.g., python:3.11-slim)'
            })

        # Environment documentation
        undocumented = [v for v in env_vars if not v['documented']]
        if undocumented:
            blockers.append({
                'severity': 'HIGH',
                'category': 'environment',
                'description': f'{len(undocumented)} undocumented environment variables',
                'estimated_fix_time_hours': 1,
                'suggestion': f"Create .env.example with: {', '.join([v['name'] for v in undocumented[:5]])}"
            })

        # Build script
        if not build_info['has_build_script']:
            blockers.append({
                'severity': 'MEDIUM',
                'category': 'build',
                'description': 'No build script detected',
                'estimated_fix_time_hours': 1,
                'suggestion': 'Add Makefile or npm build script'
            })

        return blockers

    def _compute_readiness_score(self, dockerfile, env_vars, blockers) -> int:
        """
        Score 0-10:
        - Dockerfile exists: +3
        - Dockerfile valid (no issues): +2
        - All env vars documented: +2
        - Health check present: +1
        - No critical blockers: +2
        """
        score = 0

        if dockerfile['exists']:
            score += 3
        if dockerfile.get('issues', []) == []:
            score += 2

        documented_pct = len([v for v in env_vars if v['documented']]) / len(env_vars) if env_vars else 1
        score += int(documented_pct * 2)

        critical_blockers = len([b for b in blockers if b['severity'] == 'CRITICAL'])
        if critical_blockers == 0:
            score += 2

        return min(10, score)

    def _generate_mvp_checklist(self, blockers, dockerfile, env_vars) -> List[Dict]:
        """Generate actionable checklist"""
        checklist = []

        # Map blockers to tasks
        for blocker in blockers:
            status = 'blocked' if blocker['severity'] == 'CRITICAL' else 'missing'
            checklist.append({
                'task': blocker['suggestion'].split('.')[0],  # first sentence
                'status': status,
                'time_hours': blocker['estimated_fix_time_hours']
            })

        # Standard MVP tasks
        checklist.append({'task': 'Test local deployment', 'status': 'pending', 'time_hours': 1})
        checklist.append({'task': 'Document deployment process', 'status': 'pending', 'time_hours': 0.5})

        return checklist

    def _generate_instructions(self, platform: str, dockerfile: Dict) -> str:
        """Generate deployment instructions"""
        if platform == 'docker_generic':
            return """# Deployment Instructions

1. Build Docker image: `docker build -t project-name .`
2. Test locally: `docker run -p 8080:8080 project-name`
3. Deploy to borg.tools:
   ```bash
   scp Dockerfile vizi@borg.tools:~/projects/project-name/
   ssh vizi@borg.tools 'cd ~/projects/project-name && docker build -t project-name . && docker run -d -p 8080:8080 project-name'
   ```
"""
        else:
            return f"# Platform: {platform}\n(Deployment instructions not yet implemented for this platform)"

# Entry point
def detect_deployment(project_path: str, languages: List[str], facts: Dict) -> Dict[str, Any]:
    detector = DeploymentDetector()
    return detector.analyze(Path(project_path), languages, facts)
```

## Test Criteria

### Unit Tests
```python
def test_dockerfile_parser():
    """Parse valid Dockerfile"""
    dockerfile_content = '''
FROM python:3.11-slim
EXPOSE 8080
ENV DATABASE_URL=postgres://localhost
    '''
    # Write to temp file, parse, assert
    assert result['base_image'] == 'python:3.11-slim'
    assert result['ports'] == [8080]

def test_env_var_detection():
    """Detect environment variables in Python code"""
    code = "db_url = os.getenv('DATABASE_URL')"
    env_vars = EnvironmentDetector().detect_from_code(code, 'python')
    assert 'DATABASE_URL' in [v['name'] for v in env_vars]

def test_readiness_score():
    """Score 10/10 for perfect setup"""
    # Mock data: Dockerfile exists, all env documented, no blockers
    score = DeploymentDetector()._compute_readiness_score(...)
    assert score == 10
```

### Integration Test
```bash
python -c "
from deployment_detector import detect_deployment
result = detect_deployment('/path/to/project', ['python'], {'deps': {}})
assert 'deployment' in result
assert result['deployment']['readiness_score'] >= 0
print('✅ Deployment detector test PASSED')
"
```

## Edge Cases
1. **No Dockerfile but serverless.yml**: Correctly infer serverless platform
2. **Multiple Dockerfiles**: Parse the one in root directory
3. **Invalid YAML in docker-compose**: Catch parse errors, return partial results
4. **Env vars in config files**: Extend detection beyond os.getenv()

## Libraries Required
```bash
pip install pyyaml  # for docker-compose parsing
```

## Output File
`modules/deployment_detector.py`

## Success Criteria
- ✅ Detects deployment type accurately (Docker/Serverless/Static)
- ✅ Identifies all environment variables used in code
- ✅ Computes realistic readiness score (validated on test projects)
- ✅ Generates actionable blocker list with time estimates
- ✅ Runs in <10s per project

---

**Created by The Collective Borg.tools**
**Task Owner**: Deployment Detector Session (Parallel Track 2)

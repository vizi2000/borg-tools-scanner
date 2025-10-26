"""
Deployment Detection System
Automatically detects deployment type, readiness, and generates actionable MVP checklist.

Created by The Collective Borg.tools
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import re
import json


class DockerfileParser:
    """Parse Dockerfile and extract deployment-critical information"""

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

        try:
            content = dockerfile_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            return {'exists': True, 'parse_error': str(e)}

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
            # Check for other deprecated images
            if any(dep in img for dep in ['node:8', 'node:10', 'ubuntu:14', 'alpine:3.4']):
                issues.append('deprecated_or_unpinned_base_image')

        return {
            'exists': True,
            'base_image': base_image.group(1) if base_image else None,
            'ports': [int(p) for p in ports],
            'env_vars': dict(env_vars),
            'issues': issues
        }


class DockerComposeParser:
    """Parse docker-compose.yml and extract service architecture"""

    def parse(self, compose_path: Path) -> Dict[str, Any]:
        """
        Extract services, dependencies, networks, volumes
        """
        if not compose_path.exists():
            return {'exists': False}

        try:
            import yaml
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
        except ImportError:
            return {'exists': True, 'parse_error': 'PyYAML not installed - run: pip install pyyaml'}
        except Exception as e:
            return {'exists': True, 'parse_error': str(e)}


class EnvironmentDetector:
    """Detect environment variables used in code"""

    def detect_env_vars(self, project_path: Path) -> List[Dict]:
        """
        Scan code for os.getenv(), process.env, config.get() patterns
        Check if .env.example exists
        """
        env_vars = set()

        # Python: os.getenv, os.environ.get, os.environ[]
        for py_file in project_path.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                # Pattern: os.getenv('VAR_NAME') or os.environ['VAR_NAME']
                matches = re.findall(r'os\.(?:getenv|environ\.get)\([\'"](\w+)[\'"]', content)
                env_vars.update(matches)
                # Pattern: os.environ['VAR_NAME']
                matches = re.findall(r'os\.environ\[[\'"](\w+)[\'"]\]', content)
                env_vars.update(matches)
            except Exception:
                continue

        # JavaScript/TypeScript: process.env.VAR_NAME
        for js_file in project_path.rglob('*.js'):
            try:
                content = js_file.read_text(encoding='utf-8', errors='ignore')
                matches = re.findall(r'process\.env\.(\w+)', content)
                env_vars.update(matches)
            except Exception:
                continue

        for ts_file in project_path.rglob('*.ts'):
            try:
                content = ts_file.read_text(encoding='utf-8', errors='ignore')
                matches = re.findall(r'process\.env\.(\w+)', content)
                env_vars.update(matches)
            except Exception:
                continue

        # Check documentation
        env_example = project_path / '.env.example'
        documented_vars = set()
        if env_example.exists():
            try:
                documented_vars = set(re.findall(r'^(\w+)=', env_example.read_text(), re.MULTILINE))
            except Exception:
                pass

        return [
            {
                'name': var,
                'required': True,  # heuristic: all detected vars assumed required
                'documented': var in documented_vars
            }
            for var in sorted(env_vars)
        ]


class BuildValidator:
    """Validate build configuration and scripts"""

    def validate(self, project_path: Path, languages: List[str]) -> Dict[str, Any]:
        """
        Check for build scripts:
        - Python: setup.py, pyproject.toml build config
        - Node: package.json scripts.build
        - Makefile
        """
        results = {'has_build_script': False, 'build_command': None, 'build_success_testable': False}

        # Python
        if 'python' in languages:
            if (project_path / 'setup.py').exists():
                results['has_build_script'] = True
                results['build_command'] = 'python setup.py build'
                results['build_success_testable'] = True
            elif (project_path / 'pyproject.toml').exists():
                try:
                    toml = (project_path / 'pyproject.toml').read_text()
                    if '[build-system]' in toml:
                        results['has_build_script'] = True
                        results['build_command'] = 'pip install .'
                        results['build_success_testable'] = True
                except Exception:
                    pass

        # Node
        if 'nodejs' in languages or 'javascript' in languages:
            pkg_json = project_path / 'package.json'
            if pkg_json.exists():
                try:
                    data = json.loads(pkg_json.read_text())
                    if 'build' in data.get('scripts', {}):
                        results['has_build_script'] = True
                        results['build_command'] = 'npm run build'
                        results['build_success_testable'] = True
                except Exception:
                    pass

        # Makefile
        if (project_path / 'Makefile').exists():
            results['has_build_script'] = True
            results['build_command'] = 'make build'
            results['build_success_testable'] = True

        return results


class PlatformDetector:
    """Infer target deployment platform from project configuration"""

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
        elif (project_path / 'serverless.yml').exists() or (project_path / 'serverless.yaml').exists():
            return 'aws_lambda'
        elif (project_path / 'Dockerfile').exists():
            return 'borg.tools'  # Default Docker target is borg.tools
        elif (project_path / 'index.html').exists() and not deps:
            return 'static_hosting'
        else:
            return 'unknown'


class DeploymentDetector:
    """Main orchestrator for deployment detection and readiness analysis"""

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
        blockers = self._identify_blockers(dockerfile, compose, env_vars, build_info, project_path)

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
                    'requirements_txt': (project_path / 'requirements.txt').exists(),
                    'package_json': (project_path / 'package.json').exists(),
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

    def _identify_blockers(self, dockerfile, compose, env_vars, build_info, project_path: Path) -> List[Dict]:
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
                'description': f"Dockerfile uses deprecated/unpinned base image: {dockerfile.get('base_image', 'unknown')}",
                'estimated_fix_time_hours': 0.5,
                'suggestion': 'Pin to specific version (e.g., python:3.11-slim, node:18-alpine)'
            })

        # Missing ports
        if dockerfile.get('exists') and not dockerfile.get('ports'):
            blockers.append({
                'severity': 'MEDIUM',
                'category': 'dockerfile',
                'description': 'No EXPOSE directive in Dockerfile',
                'estimated_fix_time_hours': 0.25,
                'suggestion': 'Add EXPOSE <port> directive to Dockerfile'
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
            # Only add blocker if this is a compiled language or has build requirements
            blockers.append({
                'severity': 'MEDIUM',
                'category': 'build',
                'description': 'No build script detected',
                'estimated_fix_time_hours': 1,
                'suggestion': 'Add Makefile or npm build script for consistent builds'
            })

        # Health check
        if dockerfile.get('exists'):
            try:
                content = (project_path / 'Dockerfile').read_text()
                if 'HEALTHCHECK' not in content:
                    blockers.append({
                        'severity': 'LOW',
                        'category': 'dockerfile',
                        'description': 'No HEALTHCHECK directive in Dockerfile',
                        'estimated_fix_time_hours': 0.5,
                        'suggestion': 'Add HEALTHCHECK to enable container health monitoring'
                    })
            except Exception:
                pass

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

        if env_vars:
            documented_pct = len([v for v in env_vars if v['documented']]) / len(env_vars)
            score += int(documented_pct * 2)
        else:
            # No env vars is fine
            score += 2

        critical_blockers = len([b for b in blockers if b['severity'] == 'CRITICAL'])
        high_blockers = len([b for b in blockers if b['severity'] == 'HIGH'])

        if critical_blockers == 0:
            score += 2
        if high_blockers == 0:
            score += 1

        return min(10, score)

    def _generate_mvp_checklist(self, blockers, dockerfile, env_vars) -> List[Dict]:
        """Generate actionable checklist"""
        checklist = []

        # Map blockers to tasks
        for blocker in blockers:
            if blocker['severity'] == 'CRITICAL':
                status = 'blocked'
            elif blocker['severity'] == 'HIGH':
                status = 'missing'
            else:
                status = 'pending'

            # Extract first sentence or use full suggestion
            task_desc = blocker['suggestion'].split('.')[0] if '.' in blocker['suggestion'] else blocker['suggestion']

            checklist.append({
                'task': task_desc,
                'status': status,
                'time_hours': blocker['estimated_fix_time_hours']
            })

        # Mark Dockerfile as done if exists
        if dockerfile.get('exists'):
            checklist.insert(0, {'task': 'Create Dockerfile', 'status': 'done', 'time_hours': 0})

        # Standard MVP tasks
        checklist.append({'task': 'Test local deployment', 'status': 'pending', 'time_hours': 1})
        checklist.append({'task': 'Document deployment process', 'status': 'pending', 'time_hours': 0.5})

        return checklist

    def _generate_instructions(self, platform: str, dockerfile: Dict) -> str:
        """Generate deployment instructions"""
        if platform == 'borg.tools':
            return """# Deployment to borg.tools

1. Build Docker image:
   docker build -t project-name .

2. Test locally:
   docker run -p 8080:8080 project-name

3. Deploy to borg.tools:
   scp Dockerfile vizi@borg.tools:~/projects/project-name/
   ssh vizi@borg.tools 'cd ~/projects/project-name && docker build -t project-name . && docker run -d -p 8080:8080 project-name'

4. Verify deployment:
   curl https://borg.tools/project-name/health
"""
        elif platform == 'vercel':
            return """# Deployment to Vercel

1. Install Vercel CLI:
   npm i -g vercel

2. Deploy:
   vercel --prod

3. Verify deployment in Vercel dashboard
"""
        elif platform == 'aws_lambda':
            return """# Deployment to AWS Lambda

1. Package application:
   zip -r function.zip .

2. Deploy via AWS CLI:
   aws lambda update-function-code --function-name my-function --zip-file fileb://function.zip

3. Or use Serverless Framework:
   serverless deploy
"""
        elif platform == 'static_hosting':
            return """# Deployment to Static Hosting

1. Build static assets (if needed):
   npm run build

2. Deploy to GitHub Pages, Netlify, or Vercel:
   - GitHub Pages: Push to gh-pages branch
   - Netlify: netlify deploy --prod
   - Vercel: vercel --prod
"""
        else:
            return f"# Platform: {platform}\n\nDeployment instructions not yet implemented for this platform.\nPlease consult platform-specific documentation."


# Entry point
def detect_deployment(project_path: str, languages: List[str], facts: Dict) -> Dict[str, Any]:
    """
    Main entry point for deployment detection.

    Args:
        project_path: Path to project directory
        languages: List of detected languages (e.g., ['python', 'nodejs'])
        facts: Additional facts about the project (e.g., {'deps': {...}, 'has_ci': True})

    Returns:
        Dict containing deployment analysis with readiness score, blockers, and checklist
    """
    detector = DeploymentDetector()
    return detector.analyze(Path(project_path), languages, facts)

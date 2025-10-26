# Task 1C: Documentation Analyzer & Generator

## Objective
Stworzyć moduł `doc_analyzer.py` analizujący jakość istniejącej dokumentacji, wykrywający rozbieżności między dokumentacją a kodem, oraz auto-generujący brakujące sekcje.

## Priority
🔴 **CRITICAL** - Foundation dla DOCUMENTATION_SCORE

## Estimated Time
3 hours

## Dependencies
**None** - standalone module, działa równolegle z Task 1A i 1B

## Input Format
```python
{
    "project_path": "/path/to/project",
    "languages": ["python"],
    "detected_apis": [  # from code_analyzer if available
        {"method": "GET", "path": "/api/users", "file": "routes.py"}
    ],
    "entry_points": ["main.py", "app.py"]
}
```

## Output Format
```json
{
    "documentation": {
        "overall_score": 5,
        "completeness": 0.6,
        "accuracy": 0.7,
        "found_docs": {
            "readme": {
                "exists": true,
                "path": "README.md",
                "sections": ["Installation", "Usage", "Contributing"],
                "missing_sections": ["API Documentation", "Testing", "Deployment"],
                "word_count": 450,
                "last_updated": "2024-10-15"
            },
            "api_docs": {
                "exists": false,
                "detected_endpoints": 12,
                "documented_endpoints": 0
            },
            "changelog": {"exists": false},
            "contributing": {"exists": true, "path": "CONTRIBUTING.md"},
            "license": {"exists": true, "path": "LICENSE"}
        },
        "accuracy_issues": [
            {
                "type": "outdated_dependency",
                "description": "README lists 'flask==1.0' but package.json shows 'flask==2.3'",
                "severity": "MEDIUM"
            },
            {
                "type": "missing_script",
                "description": "README mentions 'npm run dev' but script not found in package.json",
                "severity": "HIGH"
            }
        ],
        "auto_generated_sections": {
            "quickstart": "# Quick Start\n\n```bash\n# Install dependencies\npip install -r requirements.txt\n\n# Run application\npython main.py\n```",
            "api_endpoints": "# API Endpoints\n\n## GET /api/users\nReturns list of users\n\n## POST /api/users\nCreate new user\n..."
        }
    }
}
```

## Implementation Details

### 1. README Parser
```python
from pathlib import Path
from typing import Dict, List, Any
import re
from datetime import datetime

class READMEParser:
    EXPECTED_SECTIONS = [
        'Installation', 'Usage', 'Configuration', 'API',
        'Testing', 'Deployment', 'Contributing', 'License'
    ]

    def parse(self, readme_path: Path) -> Dict[str, Any]:
        """
        Extract:
        - Existing sections (markdown headers)
        - Word count, code blocks count
        - Last modified timestamp
        """
        if not readme_path.exists():
            return {
                'exists': False,
                'missing_sections': self.EXPECTED_SECTIONS
            }

        content = readme_path.read_text(encoding='utf-8', errors='ignore')

        # Extract headers (# Header, ## Subheader)
        headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)

        # Normalize headers (case-insensitive matching)
        found_sections = []
        for header in headers:
            for expected in self.EXPECTED_SECTIONS:
                if expected.lower() in header.lower():
                    found_sections.append(expected)
                    break

        missing = [s for s in self.EXPECTED_SECTIONS if s not in found_sections]

        # Metadata
        word_count = len(content.split())
        code_blocks = len(re.findall(r'```', content)) // 2
        last_updated = datetime.fromtimestamp(readme_path.stat().st_mtime).isoformat()

        return {
            'exists': True,
            'path': str(readme_path),
            'sections': found_sections,
            'missing_sections': missing,
            'word_count': word_count,
            'code_blocks': code_blocks,
            'last_updated': last_updated
        }
```

### 2. API Documentation Detector
```python
class APIDocDetector:
    def detect_endpoints(self, project_path: Path, languages: List[str]) -> List[Dict]:
        """
        Detect API endpoints from code:
        - Python Flask/FastAPI: @app.route, @router.get
        - Node Express: app.get, router.post
        - Return list of endpoints with method, path, file location
        """
        endpoints = []

        # Python Flask
        if 'python' in languages:
            for py_file in project_path.rglob('*.py'):
                content = py_file.read_text(encoding='utf-8', errors='ignore')

                # Flask: @app.route('/path', methods=['GET'])
                flask_routes = re.findall(
                    r'@(?:app|router|api)\.route\([\'"]([^\'"]+)[\'"](?:.*methods=\[([^\]]+)\])?',
                    content
                )
                for path, methods in flask_routes:
                    methods_list = re.findall(r'[\'"](\w+)[\'"]', methods) if methods else ['GET']
                    for method in methods_list:
                        endpoints.append({
                            'method': method,
                            'path': path,
                            'file': str(py_file.relative_to(project_path))
                        })

                # FastAPI: @app.get("/path")
                fastapi_routes = re.findall(r'@(?:app|router)\.(get|post|put|delete|patch)\([\'"]([^\'"]+)', content)
                for method, path in fastapi_routes:
                    endpoints.append({
                        'method': method.upper(),
                        'path': path,
                        'file': str(py_file.relative_to(project_path))
                    })

        # Node.js Express
        if 'nodejs' in languages:
            for js_file in project_path.rglob('*.js'):
                content = js_file.read_text(encoding='utf-8', errors='ignore')

                # Express: app.get('/path', ...)
                express_routes = re.findall(r'(?:app|router)\.(get|post|put|delete|patch)\([\'"]([^\'"]+)', content)
                for method, path in express_routes:
                    endpoints.append({
                        'method': method.upper(),
                        'path': path,
                        'file': str(js_file.relative_to(project_path))
                    })

        return endpoints

    def check_documented(self, endpoints: List[Dict], readme_content: str) -> int:
        """Count how many endpoints are mentioned in README"""
        documented = 0
        for ep in endpoints:
            # Simple heuristic: check if path appears in README
            if ep['path'] in readme_content:
                documented += 1
        return documented
```

### 3. Accuracy Validator
```python
class DocumentationValidator:
    def validate_accuracy(self, project_path: Path, readme_content: str, facts: Dict) -> List[Dict]:
        """
        Cross-check README against actual project state:
        - Dependencies versions (README vs requirements.txt/package.json)
        - Scripts mentioned (README vs package.json scripts)
        - File paths (README references vs actual files)
        """
        issues = []

        # Check dependencies
        deps_in_readme = re.findall(r'(?:pip install|npm install)\s+([\w-]+)(?:==|@)([\d.]+)', readme_content)
        actual_deps = facts.get('deps', {})

        for dep_name, dep_version in deps_in_readme:
            for ecosystem, deps_list in actual_deps.items():
                # Simplified: check if mentioned version matches lockfile
                # (Real impl would parse requirements.txt/package.json)
                if dep_name in deps_list and dep_version not in str(deps_list):
                    issues.append({
                        'type': 'outdated_dependency',
                        'description': f"README lists '{dep_name}=={dep_version}' but project uses different version",
                        'severity': 'MEDIUM'
                    })

        # Check npm/yarn scripts
        script_commands = re.findall(r'(?:npm|yarn) run (\w+)', readme_content)
        pkg_json = project_path / 'package.json'
        if pkg_json.exists():
            import json
            data = json.loads(pkg_json.read_text())
            actual_scripts = data.get('scripts', {}).keys()
            for cmd in script_commands:
                if cmd not in actual_scripts:
                    issues.append({
                        'type': 'missing_script',
                        'description': f"README mentions 'npm run {cmd}' but script not found in package.json",
                        'severity': 'HIGH'
                    })

        # Check file references
        file_refs = re.findall(r'`([^`]+\.(?:py|js|md|txt))`', readme_content)
        for ref in file_refs:
            if not (project_path / ref).exists():
                issues.append({
                    'type': 'broken_file_reference',
                    'description': f"README references '{ref}' but file not found",
                    'severity': 'LOW'
                })

        return issues
```

### 4. Auto-Generator
```python
class DocumentationGenerator:
    def generate_quickstart(self, project_path: Path, languages: List[str], entry_points: List[str]) -> str:
        """
        Auto-generate Quick Start section based on detected setup
        """
        steps = ["# Quick Start\n"]

        # Installation
        if 'python' in languages:
            if (project_path / 'requirements.txt').exists():
                steps.append("## Installation\n```bash\npip install -r requirements.txt\n```\n")
            elif (project_path / 'pyproject.toml').exists():
                steps.append("## Installation\n```bash\npip install .\n```\n")

        if 'nodejs' in languages:
            if (project_path / 'package.json').exists():
                steps.append("## Installation\n```bash\nnpm install\n```\n")

        # Run
        if entry_points:
            entry = entry_points[0]
            if entry.endswith('.py'):
                steps.append(f"## Run\n```bash\npython {entry}\n```\n")
            elif entry == 'package.json':
                steps.append("## Run\n```bash\nnpm start\n```\n")

        return '\n'.join(steps)

    def generate_api_docs(self, endpoints: List[Dict]) -> str:
        """
        Generate API documentation from detected endpoints
        """
        if not endpoints:
            return ""

        docs = ["# API Endpoints\n"]

        # Group by path
        grouped = {}
        for ep in endpoints:
            if ep['path'] not in grouped:
                grouped[ep['path']] = []
            grouped[ep['path']].append(ep)

        for path, eps in sorted(grouped.items()):
            docs.append(f"\n## {path}\n")
            for ep in eps:
                docs.append(f"**{ep['method']}** - Defined in `{ep['file']}`\n")
                # Placeholder description
                docs.append("_Description: (auto-generated, needs manual review)_\n")

        return '\n'.join(docs)

    def generate_missing_sections(self, missing: List[str], context: Dict) -> Dict[str, str]:
        """
        Generate content for missing README sections
        """
        generated = {}

        if 'Installation' in missing:
            generated['Installation'] = self.generate_quickstart(
                context['project_path'],
                context['languages'],
                context.get('entry_points', [])
            )

        if 'API' in missing or 'API Documentation' in missing:
            if context.get('endpoints'):
                generated['API Documentation'] = self.generate_api_docs(context['endpoints'])

        if 'Testing' in missing:
            generated['Testing'] = "# Testing\n\n```bash\n# Run tests\npytest  # or npm test\n```\n"

        if 'Deployment' in missing:
            generated['Deployment'] = "# Deployment\n\n_(Auto-generated placeholder - needs manual completion)_\n"

        return generated
```

### 5. Main Orchestrator
```python
# doc_analyzer.py

from pathlib import Path
from typing import Dict, Any, List

class DocumentationAnalyzer:
    def __init__(self):
        self.readme_parser = READMEParser()
        self.api_detector = APIDocDetector()
        self.validator = DocumentationValidator()
        self.generator = DocumentationGenerator()

    def analyze(self, project_path: Path, languages: List[str], facts: Dict, entry_points: List[str] = None) -> Dict[str, Any]:
        """Main entry point"""
        print(f"📚 [DOC ANALYZER] Analyzing documentation for {project_path.name}...")

        # Parse existing docs
        readme = self.readme_parser.parse(project_path / 'README.md')

        # Detect APIs
        endpoints = self.api_detector.detect_endpoints(project_path, languages)

        readme_content = ""
        if readme['exists']:
            readme_content = (project_path / 'README.md').read_text(encoding='utf-8', errors='ignore')

        documented_apis = self.api_detector.check_documented(endpoints, readme_content) if readme['exists'] else 0

        # Validate accuracy
        accuracy_issues = []
        if readme['exists']:
            accuracy_issues = self.validator.validate_accuracy(project_path, readme_content, facts)

        # Generate missing content
        auto_generated = {}
        if readme['exists'] and readme['missing_sections']:
            context = {
                'project_path': project_path,
                'languages': languages,
                'entry_points': entry_points or ['main.py'],
                'endpoints': endpoints
            }
            auto_generated = self.generator.generate_missing_sections(readme['missing_sections'], context)

        # Compute score
        score = self._compute_documentation_score(readme, endpoints, documented_apis, accuracy_issues)

        print(f"  📊 Documentation Score: {score}/10")
        print(f"  ⚠️  Accuracy Issues: {len(accuracy_issues)}")

        return {
            'documentation': {
                'overall_score': score,
                'completeness': len(readme.get('sections', [])) / len(READMEParser.EXPECTED_SECTIONS),
                'accuracy': 1 - (len(accuracy_issues) / 10),  # 10 issues = 0 accuracy
                'found_docs': {
                    'readme': readme,
                    'api_docs': {
                        'exists': 'API' in readme.get('sections', []),
                        'detected_endpoints': len(endpoints),
                        'documented_endpoints': documented_apis
                    },
                    'changelog': {'exists': (project_path / 'CHANGELOG.md').exists()},
                    'contributing': {'exists': (project_path / 'CONTRIBUTING.md').exists()},
                    'license': {'exists': (project_path / 'LICENSE').exists()}
                },
                'accuracy_issues': accuracy_issues,
                'auto_generated_sections': auto_generated
            }
        }

    def _compute_documentation_score(self, readme, endpoints, documented_apis, issues) -> int:
        """
        Score 0-10:
        - README exists: +3
        - Completeness (all sections): +3
        - API documentation coverage: +2
        - No accuracy issues: +2
        """
        score = 0

        if readme['exists']:
            score += 3

        completeness = len(readme.get('sections', [])) / len(READMEParser.EXPECTED_SECTIONS)
        score += int(completeness * 3)

        if endpoints:
            api_coverage = documented_apis / len(endpoints)
            score += int(api_coverage * 2)

        if len(issues) == 0:
            score += 2

        return min(10, score)

# Entry point
def analyze_documentation(project_path: str, languages: List[str], facts: Dict, entry_points: List[str] = None) -> Dict[str, Any]:
    analyzer = DocumentationAnalyzer()
    return analyzer.analyze(Path(project_path), languages, facts, entry_points)
```

## Test Criteria

### Unit Tests
```python
def test_readme_parser():
    """Parse README and detect sections"""
    readme_content = "# Project\n## Installation\n## Usage\n"
    # Parse, assert sections found
    assert 'Installation' in result['sections']
    assert 'Testing' in result['missing_sections']

def test_api_detection():
    """Detect Flask routes"""
    code = '''
@app.route('/api/users', methods=['GET', 'POST'])
def users():
    pass
    '''
    endpoints = APIDocDetector().detect_from_code(code, 'python')
    assert len(endpoints) == 2
    assert endpoints[0]['path'] == '/api/users'

def test_accuracy_validation():
    """Detect outdated dependency version"""
    readme = "pip install flask==1.0"
    facts = {'deps': {'python': ['flask==2.3']}}
    issues = DocumentationValidator().validate_accuracy(Path('.'), readme, facts)
    assert len(issues) >= 1
    assert issues[0]['type'] == 'outdated_dependency'
```

### Integration Test
```bash
python -c "
from doc_analyzer import analyze_documentation
result = analyze_documentation('/path/to/project', ['python'], {})
assert 'documentation' in result
assert result['documentation']['overall_score'] >= 0
print('✅ Doc analyzer test PASSED')
"
```

## Edge Cases
1. **No README**: Return score 0, generate full auto-generated content
2. **README in different formats**: Support README.rst, README.txt
3. **Multiple READMEs**: Prioritize README.md in root
4. **Non-standard API patterns**: Catch ValueError, continue with partial results

## Libraries Required
```bash
# No external deps - pure stdlib
```

## Output File
`modules/doc_analyzer.py`

## Success Criteria
- ✅ Parses README sections accurately (90% accuracy on test set)
- ✅ Detects API endpoints in Flask/FastAPI/Express (80% recall)
- ✅ Identifies accuracy issues (outdated deps, missing scripts)
- ✅ Auto-generates useful quickstart guide
- ✅ Runs in <10s per project

---

**Created by The Collective Borg.tools**
**Task Owner**: Doc Analyzer Session (Parallel Track 3)

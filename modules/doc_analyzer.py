"""
Documentation Analyzer & Generator Module
Analyzes documentation quality, detects discrepancies, and auto-generates missing sections.

Created by The Collective Borg.tools
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import re
from datetime import datetime
import json


class READMEParser:
    """Parses README files and extracts structural information."""

    EXPECTED_SECTIONS = [
        'Installation', 'Usage', 'Configuration', 'API',
        'Testing', 'Deployment', 'Contributing', 'License'
    ]

    def parse(self, readme_path: Path) -> Dict[str, Any]:
        """
        Extract README metadata and structure.

        Args:
            readme_path: Path to README file

        Returns:
            Dictionary with exists, path, sections, missing_sections, word_count, etc.
        """
        if not readme_path.exists():
            return {
                'exists': False,
                'missing_sections': self.EXPECTED_SECTIONS.copy()
            }

        try:
            content = readme_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            return {
                'exists': False,
                'error': str(e),
                'missing_sections': self.EXPECTED_SECTIONS.copy()
            }

        # Extract headers (# Header, ## Subheader, ### etc.)
        headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)

        # Normalize headers (case-insensitive matching)
        found_sections = []
        for header in headers:
            for expected in self.EXPECTED_SECTIONS:
                if expected.lower() in header.lower():
                    if expected not in found_sections:  # Avoid duplicates
                        found_sections.append(expected)
                    break

        missing = [s for s in self.EXPECTED_SECTIONS if s not in found_sections]

        # Metadata
        word_count = len(content.split())
        code_blocks = len(re.findall(r'```', content)) // 2

        try:
            last_updated = datetime.fromtimestamp(readme_path.stat().st_mtime).isoformat()
        except Exception:
            last_updated = None

        return {
            'exists': True,
            'path': str(readme_path),
            'sections': found_sections,
            'missing_sections': missing,
            'word_count': word_count,
            'code_blocks': code_blocks,
            'last_updated': last_updated
        }


class APIDocDetector:
    """Detects API endpoints from source code and checks documentation coverage."""

    def detect_endpoints(self, project_path: Path, languages: List[str]) -> List[Dict]:
        """
        Detect API endpoints from code.

        Supports:
        - Python Flask/FastAPI: @app.route, @router.get
        - Node Express: app.get, router.post

        Args:
            project_path: Path to project root
            languages: List of detected languages

        Returns:
            List of endpoint dictionaries with method, path, file location
        """
        endpoints = []

        # Python Flask/FastAPI
        if 'python' in languages:
            try:
                for py_file in project_path.rglob('*.py'):
                    try:
                        content = py_file.read_text(encoding='utf-8', errors='ignore')

                        # Flask: @app.route('/path', methods=['GET'])
                        flask_routes = re.findall(
                            r'@(?:app|router|api|bp)\.route\([\'"]([^\'"]+)[\'"](?:.*methods=\[([^\]]+)\])?',
                            content
                        )
                        for path, methods in flask_routes:
                            methods_list = re.findall(r'[\'"](\w+)[\'"]', methods) if methods else ['GET']
                            for method in methods_list:
                                endpoints.append({
                                    'method': method.upper(),
                                    'path': path,
                                    'file': str(py_file.relative_to(project_path))
                                })

                        # FastAPI: @app.get("/path")
                        fastapi_routes = re.findall(
                            r'@(?:app|router)\.(get|post|put|delete|patch)\([\'"]([^\'"]+)',
                            content
                        )
                        for method, path in fastapi_routes:
                            endpoints.append({
                                'method': method.upper(),
                                'path': path,
                                'file': str(py_file.relative_to(project_path))
                            })
                    except Exception:
                        continue  # Skip files that can't be read
            except Exception:
                pass  # Skip if rglob fails

        # Node.js Express
        if 'nodejs' in languages or 'javascript' in languages:
            try:
                for js_file in list(project_path.rglob('*.js')) + list(project_path.rglob('*.ts')):
                    try:
                        content = js_file.read_text(encoding='utf-8', errors='ignore')

                        # Express: app.get('/path', ...)
                        express_routes = re.findall(
                            r'(?:app|router)\.(get|post|put|delete|patch)\([\'"]([^\'"]+)',
                            content
                        )
                        for method, path in express_routes:
                            endpoints.append({
                                'method': method.upper(),
                                'path': path,
                                'file': str(js_file.relative_to(project_path))
                            })
                    except Exception:
                        continue
            except Exception:
                pass

        return endpoints

    def check_documented(self, endpoints: List[Dict], readme_content: str) -> int:
        """
        Count how many endpoints are mentioned in README.

        Args:
            endpoints: List of detected endpoints
            readme_content: Content of README file

        Returns:
            Count of documented endpoints
        """
        documented = 0
        for ep in endpoints:
            # Simple heuristic: check if path appears in README
            if ep['path'] in readme_content:
                documented += 1
        return documented


class DocumentationValidator:
    """Validates documentation accuracy against actual project state."""

    def validate_accuracy(self, project_path: Path, readme_content: str, facts: Dict) -> List[Dict]:
        """
        Cross-check README against actual project state.

        Checks:
        - Dependencies versions (README vs requirements.txt/package.json)
        - Scripts mentioned (README vs package.json scripts)
        - File paths (README references vs actual files)

        Args:
            project_path: Path to project root
            readme_content: Content of README file
            facts: Project facts from other analyzers

        Returns:
            List of accuracy issues with type, description, severity
        """
        issues = []

        # Check dependencies versions
        self._check_dependencies(readme_content, facts, issues)

        # Check npm/yarn scripts
        self._check_scripts(project_path, readme_content, issues)

        # Check file references
        self._check_file_references(project_path, readme_content, issues)

        return issues

    def _check_dependencies(self, readme_content: str, facts: Dict, issues: List[Dict]):
        """Check if dependency versions in README match actual project."""
        # Python dependencies
        pip_deps = re.findall(r'(?:pip install|pip3 install)\s+([\w-]+)(?:==|>=|<=)([\d.]+)', readme_content)

        actual_deps = facts.get('deps', {})

        for dep_name, dep_version in pip_deps:
            for ecosystem, deps_list in actual_deps.items():
                if ecosystem == 'python' and isinstance(deps_list, list):
                    # Check if mentioned version differs from actual
                    dep_found = False
                    for actual_dep in deps_list:
                        if isinstance(actual_dep, str) and dep_name.lower() in actual_dep.lower():
                            dep_found = True
                            if dep_version not in actual_dep:
                                issues.append({
                                    'type': 'outdated_dependency',
                                    'description': f"README lists '{dep_name}=={dep_version}' but project may use different version",
                                    'severity': 'MEDIUM'
                                })
                            break

        # NPM dependencies
        npm_deps = re.findall(r'(?:npm install|yarn add)\s+([\w-]+)@([\d.]+)', readme_content)

        for dep_name, dep_version in npm_deps:
            for ecosystem, deps_list in actual_deps.items():
                if ecosystem == 'nodejs' and isinstance(deps_list, list):
                    dep_found = False
                    for actual_dep in deps_list:
                        if isinstance(actual_dep, str) and dep_name.lower() in actual_dep.lower():
                            dep_found = True
                            if dep_version not in actual_dep:
                                issues.append({
                                    'type': 'outdated_dependency',
                                    'description': f"README lists '{dep_name}@{dep_version}' but project may use different version",
                                    'severity': 'MEDIUM'
                                })
                            break

    def _check_scripts(self, project_path: Path, readme_content: str, issues: List[Dict]):
        """Check if scripts mentioned in README exist in package.json."""
        script_commands = re.findall(r'(?:npm|yarn) run (\w+)', readme_content)

        pkg_json = project_path / 'package.json'
        if pkg_json.exists() and script_commands:
            try:
                data = json.loads(pkg_json.read_text(encoding='utf-8', errors='ignore'))
                actual_scripts = data.get('scripts', {}).keys()

                for cmd in set(script_commands):  # Use set to avoid duplicates
                    if cmd not in actual_scripts:
                        issues.append({
                            'type': 'missing_script',
                            'description': f"README mentions 'npm run {cmd}' but script not found in package.json",
                            'severity': 'HIGH'
                        })
            except Exception:
                pass  # Skip if package.json can't be parsed

    def _check_file_references(self, project_path: Path, readme_content: str, issues: List[Dict]):
        """Check if files referenced in README actually exist."""
        # Find file references in backticks or quotes
        file_refs = re.findall(r'`([^`]+\.(?:py|js|ts|jsx|tsx|md|txt|json|yml|yaml|toml|ini|cfg|conf))`', readme_content)
        file_refs += re.findall(r'"([^"]+\.(?:py|js|ts|jsx|tsx|md|txt|json|yml|yaml|toml|ini|cfg|conf))"', readme_content)

        for ref in set(file_refs):  # Use set to avoid duplicates
            # Try both absolute and relative paths
            file_path = project_path / ref
            if not file_path.exists() and not (project_path / ref.lstrip('/')).exists():
                issues.append({
                    'type': 'broken_file_reference',
                    'description': f"README references '{ref}' but file not found",
                    'severity': 'LOW'
                })


class DocumentationGenerator:
    """Auto-generates missing documentation sections."""

    def generate_quickstart(self, project_path: Path, languages: List[str], entry_points: List[str]) -> str:
        """
        Auto-generate Quick Start section based on detected setup.

        Args:
            project_path: Path to project root
            languages: List of detected languages
            entry_points: List of entry point files

        Returns:
            Markdown formatted quickstart guide
        """
        steps = ["# Quick Start\n"]

        # Installation
        if 'python' in languages:
            if (project_path / 'requirements.txt').exists():
                steps.append("## Installation\n```bash\npip install -r requirements.txt\n```\n")
            elif (project_path / 'pyproject.toml').exists():
                steps.append("## Installation\n```bash\npip install .\n# or for development\npip install -e .\n```\n")
            elif (project_path / 'setup.py').exists():
                steps.append("## Installation\n```bash\npip install .\n```\n")

        if 'nodejs' in languages or 'javascript' in languages:
            if (project_path / 'package.json').exists():
                steps.append("## Installation\n```bash\nnpm install\n# or\nyarn install\n```\n")

        # Run
        if entry_points:
            entry = entry_points[0]
            if entry.endswith('.py'):
                steps.append(f"## Run\n```bash\npython {entry}\n```\n")
            elif entry == 'package.json' or (project_path / 'package.json').exists():
                steps.append("## Run\n```bash\nnpm start\n# or\nyarn start\n```\n")

        return '\n'.join(steps)

    def generate_api_docs(self, endpoints: List[Dict]) -> str:
        """
        Generate API documentation from detected endpoints.

        Args:
            endpoints: List of detected endpoints

        Returns:
            Markdown formatted API documentation
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
        Generate content for missing README sections.

        Args:
            missing: List of missing section names
            context: Context dictionary with project_path, languages, entry_points, endpoints

        Returns:
            Dictionary mapping section names to generated content
        """
        generated = {}

        if 'Installation' in missing or 'Usage' in missing:
            quickstart = self.generate_quickstart(
                context['project_path'],
                context['languages'],
                context.get('entry_points', [])
            )
            if 'Installation' in missing:
                generated['Installation'] = quickstart
            if 'Usage' in missing and quickstart:
                generated['Usage'] = "# Usage\n\nSee Quick Start section for basic usage.\n"

        if 'API' in missing or 'API Documentation' in missing:
            if context.get('endpoints'):
                generated['API Documentation'] = self.generate_api_docs(context['endpoints'])

        if 'Testing' in missing:
            languages = context.get('languages', [])
            if 'python' in languages:
                generated['Testing'] = "# Testing\n\n```bash\n# Run tests\npytest\n# or\npython -m pytest\n```\n"
            elif 'nodejs' in languages or 'javascript' in languages:
                generated['Testing'] = "# Testing\n\n```bash\n# Run tests\nnpm test\n# or\nyarn test\n```\n"
            else:
                generated['Testing'] = "# Testing\n\n_(Auto-generated placeholder - needs manual completion)_\n"

        if 'Deployment' in missing:
            generated['Deployment'] = "# Deployment\n\n_(Auto-generated placeholder - needs manual completion)_\n"

        if 'Configuration' in missing:
            generated['Configuration'] = "# Configuration\n\n_(Auto-generated placeholder - needs manual completion)_\n"

        if 'Contributing' in missing:
            generated['Contributing'] = "# Contributing\n\nContributions are welcome! Please feel free to submit a Pull Request.\n"

        return generated


class DocumentationAnalyzer:
    """Main orchestrator for documentation analysis."""

    def __init__(self):
        self.readme_parser = READMEParser()
        self.api_detector = APIDocDetector()
        self.validator = DocumentationValidator()
        self.generator = DocumentationGenerator()

    def analyze(self, project_path: Path, languages: List[str], facts: Dict, entry_points: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Main entry point for documentation analysis.

        Args:
            project_path: Path to project root
            languages: List of detected programming languages
            facts: Project facts from other analyzers (deps, etc.)
            entry_points: Optional list of entry point files

        Returns:
            Dictionary with documentation analysis results
        """
        print(f"📚 [DOC ANALYZER] Analyzing documentation for {project_path.name}...")

        # Parse existing docs - try multiple README variants
        readme = None
        readme_paths = ['README.md', 'README.rst', 'README.txt', 'README', 'readme.md']

        for readme_name in readme_paths:
            readme_path = project_path / readme_name
            if readme_path.exists():
                readme = self.readme_parser.parse(readme_path)
                break

        if readme is None:
            readme = {'exists': False, 'missing_sections': READMEParser.EXPECTED_SECTIONS.copy()}

        # Detect APIs
        endpoints = self.api_detector.detect_endpoints(project_path, languages)

        readme_content = ""
        if readme['exists']:
            try:
                readme_path = Path(readme['path'])
                readme_content = readme_path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                pass

        documented_apis = self.api_detector.check_documented(endpoints, readme_content) if readme['exists'] else 0

        # Validate accuracy
        accuracy_issues = []
        if readme['exists']:
            accuracy_issues = self.validator.validate_accuracy(project_path, readme_content, facts)

        # Generate missing content
        auto_generated = {}
        if readme.get('missing_sections'):
            context = {
                'project_path': project_path,
                'languages': languages,
                'entry_points': entry_points or ['main.py'],
                'endpoints': endpoints
            }
            auto_generated = self.generator.generate_missing_sections(readme['missing_sections'], context)

        # Compute scores
        score = self._compute_documentation_score(readme, endpoints, documented_apis, accuracy_issues)
        completeness = len(readme.get('sections', [])) / len(READMEParser.EXPECTED_SECTIONS) if readme['exists'] else 0.0
        accuracy = max(0.0, 1.0 - (len(accuracy_issues) / 10.0))  # 10 issues = 0 accuracy

        print(f"  📊 Documentation Score: {score}/10")
        print(f"  📈 Completeness: {completeness:.1%}")
        print(f"  🎯 Accuracy: {accuracy:.1%}")
        print(f"  ⚠️  Accuracy Issues: {len(accuracy_issues)}")
        print(f"  🔍 Detected Endpoints: {len(endpoints)}")
        print(f"  📝 Documented Endpoints: {documented_apis}")

        return {
            'documentation': {
                'overall_score': score,
                'completeness': round(completeness, 2),
                'accuracy': round(accuracy, 2),
                'found_docs': {
                    'readme': readme,
                    'api_docs': {
                        'exists': 'API' in readme.get('sections', []) or 'API Documentation' in readme.get('sections', []),
                        'detected_endpoints': len(endpoints),
                        'documented_endpoints': documented_apis
                    },
                    'changelog': {
                        'exists': (project_path / 'CHANGELOG.md').exists() or (project_path / 'CHANGELOG').exists()
                    },
                    'contributing': {
                        'exists': (project_path / 'CONTRIBUTING.md').exists() or (project_path / 'CONTRIBUTING').exists(),
                        'path': 'CONTRIBUTING.md' if (project_path / 'CONTRIBUTING.md').exists() else None
                    },
                    'license': {
                        'exists': (project_path / 'LICENSE').exists() or (project_path / 'LICENSE.md').exists() or (project_path / 'LICENSE.txt').exists(),
                        'path': 'LICENSE' if (project_path / 'LICENSE').exists() else None
                    }
                },
                'accuracy_issues': accuracy_issues,
                'auto_generated_sections': auto_generated
            }
        }

    def _compute_documentation_score(self, readme: Dict, endpoints: List[Dict], documented_apis: int, issues: List[Dict]) -> int:
        """
        Compute documentation score 0-10.

        Scoring breakdown:
        - README exists: +3
        - Completeness (all sections): +3
        - API documentation coverage: +2
        - No accuracy issues: +2

        Args:
            readme: Parsed README data
            endpoints: List of detected endpoints
            documented_apis: Count of documented endpoints
            issues: List of accuracy issues

        Returns:
            Score from 0 to 10
        """
        score = 0

        # README exists: +3 points
        if readme.get('exists'):
            score += 3

        # Completeness: up to +3 points
        if readme.get('exists'):
            completeness = len(readme.get('sections', [])) / len(READMEParser.EXPECTED_SECTIONS)
            score += int(completeness * 3)

        # API coverage: up to +2 points
        if endpoints:
            api_coverage = documented_apis / len(endpoints)
            score += int(api_coverage * 2)
        elif not endpoints:
            # If no APIs detected, give partial credit
            score += 1

        # Accuracy: up to +2 points
        if len(issues) == 0:
            score += 2
        elif len(issues) <= 2:
            score += 1

        return min(10, score)


# Entry point function
def analyze_documentation(project_path: str, languages: List[str], facts: Dict, entry_points: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Analyze project documentation quality and generate missing sections.

    Args:
        project_path: Path to project root directory
        languages: List of detected programming languages (e.g., ['python', 'javascript'])
        facts: Dictionary of project facts including dependencies
        entry_points: Optional list of entry point files

    Returns:
        Dictionary containing documentation analysis results with structure:
        {
            'documentation': {
                'overall_score': int (0-10),
                'completeness': float (0.0-1.0),
                'accuracy': float (0.0-1.0),
                'found_docs': {...},
                'accuracy_issues': [...],
                'auto_generated_sections': {...}
            }
        }
    """
    analyzer = DocumentationAnalyzer()
    return analyzer.analyze(Path(project_path), languages, facts, entry_points)

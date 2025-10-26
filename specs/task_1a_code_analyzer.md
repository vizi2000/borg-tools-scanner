# Task 1A: Deep Code Analysis Engine

## Objective
Stworzyć moduł `code_analyzer.py` wykonujący głęboką analizę statyczną kodu źródłowego projektów w celu wykrywania wzorców architektonicznych, metryk jakości, i potencjalnych problemów.

## Priority
🔴 **CRITICAL** - Foundation dla CODE_QUALITY_SCORE

## Estimated Time
4 hours

## Dependencies
**None** - standalone module, może działać równolegle z innymi Task z Grupy 1

## Input Format
```python
{
    "project_path": "/path/to/project",
    "languages": ["python", "javascript"],  # from existing detection
    "file_list": ["src/main.py", "src/api.js", ...]  # filtered files
}
```

## Output Format
```json
{
    "code_quality": {
        "overall_score": 7.5,
        "architecture_pattern": "MVC",
        "modularity_score": 8,
        "complexity_metrics": {
            "avg_cyclomatic": 4.2,
            "avg_cognitive": 6.1,
            "max_complexity_file": "src/core/engine.py",
            "max_complexity_value": 15
        },
        "readability": {
            "score": 7,
            "naming_conventions": "good",
            "avg_function_length": 12,
            "documentation_coverage": 0.45
        },
        "best_practices": {
            "error_handling_coverage": 0.65,
            "logging_present": true,
            "security_patterns": ["input_validation", "sql_parameterized"]
        },
        "debt_indicators": {
            "todo_count": 23,
            "fixme_count": 7,
            "hack_count": 2,
            "deprecated_apis": ["flask.ext", "requests.get(verify=False)"],
            "code_duplication_estimate": "medium"
        },
        "fundamental_issues": [
            {
                "severity": "HIGH",
                "category": "security",
                "description": "Hardcoded credentials detected",
                "file": "src/config.py",
                "line": 42,
                "snippet": "API_KEY = '12345abcdef'"
            }
        ]
    }
}
```

## Implementation Details

### 1. Python Analysis (using `ast` module)
```python
import ast
from pathlib import Path
from typing import Dict, List, Any

class PythonAnalyzer:
    def analyze_file(self, filepath: Path) -> Dict[str, Any]:
        """
        Parse Python file using AST and extract:
        - Function/class definitions
        - Cyclomatic complexity (count branches: if/for/while/except/and/or)
        - Cognitive complexity (nesting depth)
        - Docstring coverage
        - Import analysis (detect deprecated libraries)
        """
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        # Metrics extraction
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

        return {
            'functions': len(functions),
            'classes': len(classes),
            'avg_function_complexity': self._compute_cyclomatic(functions),
            'docstring_coverage': self._check_docstrings(functions + classes)
        }

    def _compute_cyclomatic(self, functions: List[ast.FunctionDef]) -> float:
        """
        Cyclomatic Complexity = 1 + number of decision points
        Decision points: if, for, while, except, and, or, lambda
        """
        total = 0
        for func in functions:
            complexity = 1  # base
            for node in ast.walk(func):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
            total += complexity
        return total / len(functions) if functions else 0
```

### 2. JavaScript/TypeScript Analysis (using regex + pattern matching)
```python
import re

class JavaScriptAnalyzer:
    def analyze_file(self, filepath: Path) -> Dict[str, Any]:
        """
        Basic static analysis for JS/TS:
        - Function declarations (function/arrow/async)
        - Class definitions
        - Import/export patterns
        - Framework detection (React/Vue/Angular)
        """
        content = filepath.read_text(encoding='utf-8', errors='ignore')

        # Patterns
        function_pattern = r'(function\s+\w+|const\s+\w+\s*=\s*(\([^)]*\)|async)\s*=>)'
        class_pattern = r'class\s+\w+'
        import_pattern = r'import\s+.*\s+from\s+[\'"](.+?)[\'"]'

        return {
            'functions': len(re.findall(function_pattern, content)),
            'classes': len(re.findall(class_pattern, content)),
            'imports': re.findall(import_pattern, content),
            'framework': self._detect_framework(content)
        }

    def _detect_framework(self, content: str) -> str:
        if 'React.Component' in content or 'useState' in content:
            return 'React'
        elif 'Vue.extend' in content or '<template>' in content:
            return 'Vue'
        elif '@Component' in content and '@NgModule' in content:
            return 'Angular'
        return 'vanilla'
```

### 3. Security Pattern Detection
```python
class SecurityAnalyzer:
    DANGEROUS_PATTERNS = [
        (r'API_KEY\s*=\s*[\'"][\w-]+[\'"]', 'hardcoded_credentials'),
        (r'password\s*=\s*[\'"][\w-]+[\'"]', 'hardcoded_password'),
        (r'eval\(', 'code_injection_risk'),
        (r'exec\(', 'code_execution_risk'),
        (r'verify=False', 'ssl_verification_disabled'),
        (r'SELECT.*\+.*\+', 'sql_injection_risk'),  # naive string concat in SQL
    ]

    def scan_file(self, filepath: Path) -> List[Dict]:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        issues = []

        for pattern, issue_type in self.DANGEROUS_PATTERNS:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'type': issue_type,
                    'file': str(filepath),
                    'line': line_num,
                    'snippet': match.group(0)[:100]
                })

        return issues
```

### 4. Architecture Pattern Detection
```python
class ArchitectureDetector:
    def detect_pattern(self, project_path: Path) -> str:
        """
        Heuristic detection based on directory structure:
        - MVC: models/, views/, controllers/
        - Hexagonal: domain/, application/, infrastructure/
        - Microservices: multiple main.py with separate requirements
        - Monolith: single large main.py
        """
        subdirs = [d.name for d in project_path.iterdir() if d.is_dir()]

        if {'models', 'views', 'controllers'}.issubset(subdirs):
            return 'MVC'
        elif {'domain', 'application', 'infrastructure'}.intersection(subdirs):
            return 'Hexagonal (DDD)'
        elif 'services' in subdirs and len(list(project_path.rglob('main.py'))) > 1:
            return 'Microservices'
        elif len(list(project_path.rglob('*.py'))) > 50:
            return 'Monolith'
        else:
            return 'Flat/Simple'
```

### 5. Main Orchestrator
```python
# code_analyzer.py

from pathlib import Path
from typing import Dict, Any
import json

class CodeAnalyzer:
    def __init__(self):
        self.python_analyzer = PythonAnalyzer()
        self.js_analyzer = JavaScriptAnalyzer()
        self.security_analyzer = SecurityAnalyzer()
        self.arch_detector = ArchitectureDetector()

    def analyze_project(self, project_path: Path, languages: List[str]) -> Dict[str, Any]:
        """Main entry point for code analysis"""
        print(f"🔍 [CODE ANALYZER] Scanning {project_path.name}...")

        results = {
            'architecture_pattern': self.arch_detector.detect_pattern(project_path),
            'languages': {},
            'security_issues': [],
            'overall_metrics': {}
        }

        # Analyze by language
        if 'python' in languages:
            py_files = list(project_path.rglob('*.py'))
            print(f"  📄 Analyzing {len(py_files)} Python files...")
            results['languages']['python'] = self._analyze_python_files(py_files)

        if 'nodejs' in languages or 'javascript' in languages:
            js_files = list(project_path.rglob('*.js')) + list(project_path.rglob('*.ts'))
            print(f"  📄 Analyzing {len(js_files)} JS/TS files...")
            results['languages']['javascript'] = self._analyze_js_files(js_files)

        # Security scan (all text files)
        print(f"  🔒 Running security scan...")
        all_files = [f for f in project_path.rglob('*') if f.is_file() and f.suffix in ['.py', '.js', '.ts', '.java', '.go']]
        for file in all_files[:100]:  # limit to 100 files for performance
            results['security_issues'].extend(self.security_analyzer.scan_file(file))

        # Compute overall score
        results['overall_metrics'] = self._compute_overall_score(results)

        print(f"  ✅ Analysis complete. Score: {results['overall_metrics']['code_quality_score']}/10")
        return results

    def _compute_overall_score(self, results: Dict) -> Dict:
        """
        CODE_QUALITY_SCORE = weighted average of:
        - Architecture (20%): pattern detected, modularity
        - Complexity (25%): avg cyclomatic, cognitive
        - Readability (20%): naming, docs, function length
        - Best Practices (20%): error handling, logging, security
        - Debt (15%): TODO count, deprecated APIs, duplicates
        """
        # Simplified scoring logic
        arch_score = 8 if results['architecture_pattern'] != 'Flat/Simple' else 5
        complexity_score = 10 - min(10, avg_complexity / 2)  # lower complexity = higher score
        security_score = 10 - min(10, len(results['security_issues']))

        overall = (arch_score * 0.2 + complexity_score * 0.25 + security_score * 0.35 + 7 * 0.2)
        return {
            'code_quality_score': round(overall, 1),
            'breakdown': {
                'architecture': arch_score,
                'complexity': complexity_score,
                'security': security_score
            }
        }

# Entry point for integration
def analyze_code(project_path: str, languages: List[str]) -> Dict[str, Any]:
    analyzer = CodeAnalyzer()
    return analyzer.analyze_project(Path(project_path), languages)
```

## Test Criteria

### Unit Tests
```python
# tests/test_code_analyzer.py
def test_python_cyclomatic_complexity():
    """Verify cyclomatic complexity calculation for simple function"""
    code = '''
def example(x):
    if x > 0:
        return x
    elif x < 0:
        return -x
    else:
        return 0
    '''
    # Expected: 1 (base) + 2 (if, elif) = 3
    assert compute_cyclomatic(code) == 3

def test_security_pattern_detection():
    """Detect hardcoded API key"""
    code = "API_KEY = 'sk-1234567890abcdef'"
    issues = SecurityAnalyzer().scan_content(code)
    assert len(issues) == 1
    assert issues[0]['type'] == 'hardcoded_credentials'

def test_architecture_detection_mvc():
    """Detect MVC pattern from directory structure"""
    # Create temp directory with models/, views/, controllers/
    assert ArchitectureDetector().detect_pattern(temp_path) == 'MVC'
```

### Integration Test
```bash
# Test on sample project
python -c "
from code_analyzer import analyze_code
result = analyze_code('/Users/wojciechwiesner/ai/sample-project', ['python'])
assert 'code_quality' in result
assert result['code_quality']['overall_score'] >= 0
assert result['code_quality']['overall_score'] <= 10
print('✅ Code analyzer test PASSED')
"
```

## Edge Cases to Handle

1. **Large Files**: Skip files >1MB to avoid memory issues
2. **Binary Files**: Detect and skip (check for null bytes)
3. **Encoding Issues**: Use `errors='ignore'` when reading
4. **Empty Projects**: Return default scores (0) with warning
5. **Mixed Languages**: Aggregate scores across multiple language analyzers
6. **AST Parse Errors**: Catch SyntaxError, return partial results

## Libraries Required
```bash
pip install ast  # built-in
# No external deps needed for MVP - pure stdlib
```

## Output File
`modules/code_analyzer.py` - ready to import in main scanner

## Success Criteria
- ✅ Accurately detects architecture pattern (90% accuracy on test set)
- ✅ Computes cyclomatic complexity for Python (verified vs known tools)
- ✅ Identifies critical security issues (hardcoded secrets, SQL injection patterns)
- ✅ Returns valid JSON matching output schema
- ✅ Runs in <30s for typical project (500 files)

---

**Created by The Collective Borg.tools**
**Task Owner**: Code Analyzer Session (Parallel Track 1)

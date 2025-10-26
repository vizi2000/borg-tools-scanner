"""
Unit Tests for Deep Code Analysis Engine

Tests all components of the code analyzer:
- PythonAnalyzer (AST-based)
- JavaScriptAnalyzer (regex-based)
- SecurityAnalyzer (vulnerability detection)
- ArchitectureDetector (pattern recognition)
- CodeAnalyzer (main orchestrator)

Created by The Collective Borg.tools
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.code_analyzer import (
    PythonAnalyzer,
    JavaScriptAnalyzer,
    SecurityAnalyzer,
    ArchitectureDetector,
    CodeAnalyzer,
    analyze_code
)


class TestPythonAnalyzer(unittest.TestCase):
    """Test Python AST-based analysis"""

    def setUp(self):
        self.analyzer = PythonAnalyzer()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_cyclomatic_complexity_simple(self):
        """Test cyclomatic complexity for simple function"""
        code = '''
def simple_function(x):
    return x + 1
'''
        file_path = Path(self.temp_dir) / 'test.py'
        file_path.write_text(code)

        result = self.analyzer.analyze_file(file_path)

        self.assertEqual(result['functions'], 1)
        # Simple function: complexity = 1 (base)
        self.assertEqual(result['avg_cyclomatic'], 1)

    def test_cyclomatic_complexity_with_branches(self):
        """Test cyclomatic complexity with multiple branches"""
        code = '''
def example(x):
    if x > 0:
        return x
    elif x < 0:
        return -x
    else:
        return 0
'''
        file_path = Path(self.temp_dir) / 'test.py'
        file_path.write_text(code)

        result = self.analyzer.analyze_file(file_path)

        # Expected: 1 (base) + 2 (if, elif) = 3
        self.assertEqual(result['avg_cyclomatic'], 3)

    def test_docstring_coverage(self):
        """Test docstring coverage calculation"""
        code = '''
def documented():
    """This function has a docstring"""
    pass

def undocumented():
    pass

class DocumentedClass:
    """This class has a docstring"""
    pass
'''
        file_path = Path(self.temp_dir) / 'test.py'
        file_path.write_text(code)

        result = self.analyzer.analyze_file(file_path)

        self.assertEqual(result['functions'], 2)
        self.assertEqual(result['classes'], 1)
        # 2 out of 3 items documented = 0.67
        self.assertAlmostEqual(result['docstring_coverage'], 0.67, places=2)

    def test_import_detection(self):
        """Test import statement detection"""
        code = '''
import os
import sys
from pathlib import Path
from typing import Dict, List
'''
        file_path = Path(self.temp_dir) / 'test.py'
        file_path.write_text(code)

        result = self.analyzer.analyze_file(file_path)

        self.assertIn('os', result['imports'])
        self.assertIn('sys', result['imports'])
        self.assertIn('pathlib', result['imports'])
        self.assertIn('typing', result['imports'])

    def test_deprecated_import_detection(self):
        """Test detection of deprecated imports"""
        code = '''
from flask.ext import wtf
import imp
'''
        file_path = Path(self.temp_dir) / 'test.py'
        file_path.write_text(code)

        result = self.analyzer.analyze_file(file_path)

        self.assertTrue(len(result['deprecated_imports']) > 0)
        self.assertTrue(any('flask.ext' in imp or 'imp' in imp for imp in result['deprecated_imports']))

    def test_syntax_error_handling(self):
        """Test handling of files with syntax errors"""
        code = '''
def broken_function(
    # Missing closing parenthesis
'''
        file_path = Path(self.temp_dir) / 'test.py'
        file_path.write_text(code)

        result = self.analyzer.analyze_file(file_path)

        # Should return error result without crashing
        self.assertIn('error', result)
        self.assertEqual(result['functions'], 0)


class TestJavaScriptAnalyzer(unittest.TestCase):
    """Test JavaScript/TypeScript regex-based analysis"""

    def setUp(self):
        self.analyzer = JavaScriptAnalyzer()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_function_detection(self):
        """Test detection of various function declarations"""
        code = '''
function regularFunction() {
    return 42;
}

const arrowFunction = () => {
    return 100;
};

async function asyncFunction() {
    return await fetch();
}
'''
        file_path = Path(self.temp_dir) / 'test.js'
        file_path.write_text(code)

        result = self.analyzer.analyze_file(file_path)

        self.assertEqual(result['functions'], 3)

    def test_class_detection(self):
        """Test class detection"""
        code = '''
class MyClass {
    constructor() {
        this.value = 0;
    }
}

class AnotherClass extends MyClass {
    method() {}
}
'''
        file_path = Path(self.temp_dir) / 'test.js'
        file_path.write_text(code)

        result = self.analyzer.analyze_file(file_path)

        self.assertEqual(result['classes'], 2)

    def test_react_detection(self):
        """Test React framework detection"""
        code = '''
import React, { useState, useEffect } from 'react';

function MyComponent() {
    const [state, setState] = useState(0);
    return <div>Hello</div>;
}
'''
        file_path = Path(self.temp_dir) / 'test.jsx'
        file_path.write_text(code)

        result = self.analyzer.analyze_file(file_path)

        self.assertEqual(result['framework'], 'React')
        self.assertTrue(result['has_jsx'])

    def test_typescript_detection(self):
        """Test TypeScript file detection"""
        code = '''
interface User {
    name: string;
    age: number;
}

const user: User = { name: "John", age: 30 };
'''
        file_path = Path(self.temp_dir) / 'test.ts'
        file_path.write_text(code)

        result = self.analyzer.analyze_file(file_path)

        self.assertTrue(result['has_typescript'])


class TestSecurityAnalyzer(unittest.TestCase):
    """Test security vulnerability detection"""

    def setUp(self):
        self.analyzer = SecurityAnalyzer()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_hardcoded_credentials_detection(self):
        """Test detection of hardcoded API keys"""
        code = '''
API_KEY = "sk-1234567890abcdef"
SECRET = "my-secret-key-123"
'''
        file_path = Path(self.temp_dir) / 'config.py'
        file_path.write_text(code)

        issues = self.analyzer.scan_file(file_path)

        self.assertTrue(len(issues) >= 1)
        self.assertTrue(any(issue['type'] == 'hardcoded_credentials' for issue in issues))

    def test_sql_injection_detection(self):
        """Test detection of SQL injection vulnerabilities"""
        code = '''
query = "SELECT * FROM users WHERE id = " + user_id + " AND active = 1"
cursor.execute("SELECT * FROM users WHERE name = '%s'" % username)
'''
        file_path = Path(self.temp_dir) / 'db.py'
        file_path.write_text(code)

        issues = self.analyzer.scan_file(file_path)

        sql_issues = [issue for issue in issues if issue['type'] == 'sql_injection_risk']
        self.assertTrue(len(sql_issues) >= 1)

    def test_code_execution_detection(self):
        """Test detection of dangerous code execution functions"""
        code = '''
eval(user_input)
exec(untrusted_code)
'''
        file_path = Path(self.temp_dir) / 'dangerous.py'
        file_path.write_text(code)

        issues = self.analyzer.scan_file(file_path)

        self.assertTrue(any(issue['type'] == 'code_injection_risk' for issue in issues))
        self.assertTrue(any(issue['type'] == 'code_execution_risk' for issue in issues))

    def test_ssl_verification_disabled(self):
        """Test detection of disabled SSL verification"""
        code = '''
import requests
response = requests.get("https://example.com", verify=False)
'''
        file_path = Path(self.temp_dir) / 'http_client.py'
        file_path.write_text(code)

        issues = self.analyzer.scan_file(file_path)

        self.assertTrue(any(issue['type'] == 'ssl_verification_disabled' for issue in issues))

    def test_severity_levels(self):
        """Test that issues have correct severity levels"""
        code = '''
API_KEY = "hardcoded-key-12345"
import random
x = random.random()
'''
        file_path = Path(self.temp_dir) / 'test.py'
        file_path.write_text(code)

        issues = self.analyzer.scan_file(file_path)

        # Hardcoded credentials should be HIGH
        high_issues = [issue for issue in issues if issue['severity'] == 'HIGH']
        low_issues = [issue for issue in issues if issue['severity'] == 'LOW']

        self.assertTrue(len(high_issues) > 0)


class TestArchitectureDetector(unittest.TestCase):
    """Test architecture pattern detection"""

    def setUp(self):
        self.detector = ArchitectureDetector()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_mvc_detection(self):
        """Test MVC pattern detection"""
        # Create MVC directory structure
        project_path = Path(self.temp_dir) / 'mvc_project'
        project_path.mkdir()
        (project_path / 'models').mkdir()
        (project_path / 'views').mkdir()
        (project_path / 'controllers').mkdir()

        pattern = self.detector.detect_pattern(project_path)

        self.assertEqual(pattern, 'MVC')

    def test_django_detection(self):
        """Test Django pattern detection"""
        project_path = Path(self.temp_dir) / 'django_project'
        project_path.mkdir()
        (project_path / 'manage.py').write_text('# Django management script')

        pattern = self.detector.detect_pattern(project_path)

        self.assertEqual(pattern, 'Django (MVT)')

    def test_hexagonal_detection(self):
        """Test Hexagonal architecture detection"""
        project_path = Path(self.temp_dir) / 'hex_project'
        project_path.mkdir()
        (project_path / 'domain').mkdir()
        (project_path / 'application').mkdir()
        (project_path / 'infrastructure').mkdir()

        pattern = self.detector.detect_pattern(project_path)

        self.assertIn('Hexagonal', pattern)

    def test_flat_structure_detection(self):
        """Test flat/simple structure detection"""
        project_path = Path(self.temp_dir) / 'simple_project'
        project_path.mkdir()
        (project_path / 'main.py').write_text('print("Hello")')
        (project_path / 'utils.py').write_text('def helper(): pass')

        pattern = self.detector.detect_pattern(project_path)

        self.assertEqual(pattern, 'Flat/Simple')


class TestCodeAnalyzer(unittest.TestCase):
    """Test main code analyzer orchestrator"""

    def setUp(self):
        self.analyzer = CodeAnalyzer()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_analyze_python_project(self):
        """Test analysis of a simple Python project"""
        project_path = Path(self.temp_dir) / 'test_project'
        project_path.mkdir()

        # Create some Python files
        (project_path / 'main.py').write_text('''
def main():
    """Main function"""
    print("Hello, World!")

if __name__ == "__main__":
    main()
''')

        (project_path / 'utils.py').write_text('''
def helper(x):
    if x > 0:
        return x * 2
    return 0
''')

        result = self.analyzer.analyze_project(project_path, ['python'])

        self.assertIn('code_quality', result)
        self.assertIn('overall_score', result['code_quality'])
        self.assertGreaterEqual(result['code_quality']['overall_score'], 0)
        self.assertLessEqual(result['code_quality']['overall_score'], 10)

    def test_score_calculation(self):
        """Test that overall score is calculated correctly"""
        project_path = Path(self.temp_dir) / 'test_project'
        project_path.mkdir()
        (project_path / 'models').mkdir()
        (project_path / 'views').mkdir()
        (project_path / 'controllers').mkdir()

        # Create a well-documented file
        (project_path / 'models' / 'user.py').write_text('''
def get_user(user_id):
    """Retrieve user by ID"""
    return {"id": user_id, "name": "Test"}

def save_user(user):
    """Save user to database"""
    pass
''')

        result = self.analyzer.analyze_project(project_path, ['python'])

        # MVC pattern should give good architecture score
        self.assertEqual(result['code_quality']['architecture_pattern'], 'MVC')
        self.assertGreaterEqual(result['code_quality']['modularity_score'], 7)

    def test_entry_point_function(self):
        """Test the analyze_code entry point function"""
        project_path = Path(self.temp_dir) / 'test_project'
        project_path.mkdir()

        (project_path / 'app.py').write_text('''
def app():
    """Application entry point"""
    return "Running"
''')

        result = analyze_code(str(project_path), ['python'])

        self.assertIn('code_quality', result)
        self.assertIsInstance(result['code_quality']['overall_score'], (int, float))

    def test_security_issue_reporting(self):
        """Test that security issues are reported in fundamental_issues"""
        project_path = Path(self.temp_dir) / 'test_project'
        project_path.mkdir()

        (project_path / 'config.py').write_text('''
API_KEY = "sk-hardcoded-key-12345"
password = "admin123"
''')

        result = self.analyzer.analyze_project(project_path, ['python'])

        fundamental_issues = result['code_quality']['fundamental_issues']
        self.assertTrue(len(fundamental_issues) > 0)
        self.assertTrue(any(issue['severity'] == 'HIGH' for issue in fundamental_issues))

    def test_empty_project(self):
        """Test handling of empty project"""
        project_path = Path(self.temp_dir) / 'empty_project'
        project_path.mkdir()

        result = self.analyzer.analyze_project(project_path, ['python'])

        # Should not crash, should return valid result
        self.assertIn('code_quality', result)
        self.assertIsInstance(result['code_quality']['overall_score'], (int, float))


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflow"""

    def test_output_schema_validity(self):
        """Test that output matches the expected JSON schema"""
        temp_dir = tempfile.mkdtemp()

        try:
            project_path = Path(temp_dir) / 'test_project'
            project_path.mkdir()

            (project_path / 'main.py').write_text('def main(): pass')

            result = analyze_code(str(project_path), ['python'])

            # Verify schema structure
            self.assertIn('code_quality', result)
            code_quality = result['code_quality']

            required_fields = [
                'overall_score',
                'architecture_pattern',
                'modularity_score',
                'complexity_metrics',
                'readability',
                'best_practices',
                'debt_indicators',
                'fundamental_issues'
            ]

            for field in required_fields:
                self.assertIn(field, code_quality, f"Missing required field: {field}")

            # Verify nested structures
            self.assertIn('avg_cyclomatic', code_quality['complexity_metrics'])
            self.assertIn('score', code_quality['readability'])
            self.assertIn('todo_count', code_quality['debt_indicators'])

        finally:
            shutil.rmtree(temp_dir)


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPythonAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestJavaScriptAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestArchitectureDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

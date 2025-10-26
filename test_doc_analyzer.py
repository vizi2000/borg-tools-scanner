#!/usr/bin/env python3
"""
Test script for doc_analyzer module
Tests all major functionality with sample data
"""

import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'modules'))

from doc_analyzer import (
    READMEParser,
    APIDocDetector,
    DocumentationValidator,
    DocumentationGenerator,
    analyze_documentation
)


def test_readme_parser():
    """Test README parsing functionality."""
    print("\n=== TEST 1: README Parser ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        readme = tmppath / 'README.md'

        # Create sample README
        readme.write_text("""
# Test Project

## Installation

Run `pip install -r requirements.txt`

## Usage

Just run `python main.py`

## Contributing

Send PRs!

## License

MIT License
""")

        parser = READMEParser()
        result = parser.parse(readme)

        print(f"✓ README exists: {result['exists']}")
        print(f"✓ Sections found: {result['sections']}")
        print(f"✓ Missing sections: {result['missing_sections']}")
        print(f"✓ Word count: {result['word_count']}")

        assert result['exists'] == True
        assert 'Installation' in result['sections']
        assert 'Usage' in result['sections']
        assert 'Testing' in result['missing_sections']
        assert 'API' in result['missing_sections']

        print("✅ README Parser test PASSED")


def test_api_detection():
    """Test API endpoint detection."""
    print("\n=== TEST 2: API Detection ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create sample Flask app
        flask_app = tmppath / 'app.py'
        flask_app.write_text("""
from flask import Flask

app = Flask(__name__)

@app.route('/api/users', methods=['GET', 'POST'])
def users():
    pass

@app.route('/api/users/<id>', methods=['GET'])
def user_detail(id):
    pass
""")

        # Create sample FastAPI app
        fastapi_app = tmppath / 'main.py'
        fastapi_app.write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/items")
def list_items():
    pass

@app.post("/api/items")
def create_item():
    pass
""")

        detector = APIDocDetector()
        endpoints = detector.detect_endpoints(tmppath, ['python'])

        print(f"✓ Total endpoints detected: {len(endpoints)}")
        for ep in endpoints:
            print(f"  - {ep['method']} {ep['path']} ({ep['file']})")

        assert len(endpoints) >= 4
        methods = [ep['method'] for ep in endpoints]
        assert 'GET' in methods
        assert 'POST' in methods

        print("✅ API Detection test PASSED")


def test_accuracy_validation():
    """Test documentation accuracy validation."""
    print("\n=== TEST 3: Accuracy Validation ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create README with outdated info
        readme = tmppath / 'README.md'
        readme.write_text("""
# Project

Install with: `pip install flask==1.0.0`

Run with: `npm run dev`

See `config.py` for configuration.
""")

        # Create package.json without 'dev' script
        pkg_json = tmppath / 'package.json'
        pkg_json.write_text('{"scripts": {"start": "node index.js"}}')

        # Simulate facts with different Flask version
        facts = {
            'deps': {
                'python': ['flask==2.3.0', 'requests==2.28.0']
            }
        }

        validator = DocumentationValidator()
        readme_content = readme.read_text()
        issues = validator.validate_accuracy(tmppath, readme_content, facts)

        print(f"✓ Issues detected: {len(issues)}")
        for issue in issues:
            print(f"  - [{issue['severity']}] {issue['type']}: {issue['description']}")

        # Should detect:
        # 1. Outdated dependency (flask 1.0 vs 2.3)
        # 2. Missing script (npm run dev)
        # 3. Broken file reference (config.py doesn't exist)
        assert len(issues) >= 2

        print("✅ Accuracy Validation test PASSED")


def test_documentation_generator():
    """Test auto-generation of documentation."""
    print("\n=== TEST 4: Documentation Generator ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create requirements.txt
        (tmppath / 'requirements.txt').write_text('flask==2.0.0\nrequests==2.28.0')

        # Create sample endpoints
        endpoints = [
            {'method': 'GET', 'path': '/api/users', 'file': 'app.py'},
            {'method': 'POST', 'path': '/api/users', 'file': 'app.py'},
            {'method': 'GET', 'path': '/api/users/<id>', 'file': 'app.py'},
        ]

        generator = DocumentationGenerator()

        # Test quickstart generation
        quickstart = generator.generate_quickstart(tmppath, ['python'], ['main.py'])
        print(f"✓ Generated quickstart:\n{quickstart[:200]}...")
        assert 'pip install' in quickstart
        assert 'python' in quickstart

        # Test API docs generation
        api_docs = generator.generate_api_docs(endpoints)
        print(f"\n✓ Generated API docs:\n{api_docs[:300]}...")
        assert '/api/users' in api_docs
        assert 'GET' in api_docs
        assert 'POST' in api_docs

        # Test missing sections generation
        missing = ['Installation', 'API Documentation', 'Testing']
        context = {
            'project_path': tmppath,
            'languages': ['python'],
            'entry_points': ['main.py'],
            'endpoints': endpoints
        }
        generated = generator.generate_missing_sections(missing, context)

        print(f"\n✓ Generated sections: {list(generated.keys())}")
        assert 'Installation' in generated
        assert 'API Documentation' in generated
        assert 'Testing' in generated

        print("✅ Documentation Generator test PASSED")


def test_full_analysis():
    """Test complete documentation analysis workflow."""
    print("\n=== TEST 5: Full Analysis ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a realistic project structure
        readme = tmppath / 'README.md'
        readme.write_text("""
# Sample Project

A sample Flask API project.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the server:
```bash
python app.py
```

## License

MIT
""")

        # Create Flask app
        app_py = tmppath / 'app.py'
        app_py.write_text("""
from flask import Flask

app = Flask(__name__)

@app.route('/api/hello')
def hello():
    return 'Hello'

@app.route('/api/users', methods=['GET', 'POST'])
def users():
    pass
""")

        # Create requirements.txt
        (tmppath / 'requirements.txt').write_text('flask==2.0.0')

        # Create LICENSE
        (tmppath / 'LICENSE').write_text('MIT License')

        # Run full analysis
        result = analyze_documentation(
            str(tmppath),
            ['python'],
            {'deps': {'python': ['flask==2.0.0']}},
            ['app.py']
        )

        print(f"\n✓ Overall score: {result['documentation']['overall_score']}/10")
        print(f"✓ Completeness: {result['documentation']['completeness']:.2%}")
        print(f"✓ Accuracy: {result['documentation']['accuracy']:.2%}")
        print(f"✓ README exists: {result['documentation']['found_docs']['readme']['exists']}")
        print(f"✓ Detected endpoints: {result['documentation']['found_docs']['api_docs']['detected_endpoints']}")
        print(f"✓ Issues: {len(result['documentation']['accuracy_issues'])}")

        assert 'documentation' in result
        assert result['documentation']['overall_score'] >= 0
        assert result['documentation']['overall_score'] <= 10
        assert result['documentation']['found_docs']['readme']['exists'] == True
        assert result['documentation']['found_docs']['license']['exists'] == True
        assert result['documentation']['found_docs']['api_docs']['detected_endpoints'] >= 2

        print("✅ Full Analysis test PASSED")


def main():
    """Run all tests."""
    print("=" * 60)
    print("DOCUMENTATION ANALYZER TEST SUITE")
    print("=" * 60)

    try:
        test_readme_parser()
        test_api_detection()
        test_accuracy_validation()
        test_documentation_generator()
        test_full_analysis()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

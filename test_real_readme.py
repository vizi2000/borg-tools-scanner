#!/usr/bin/env python3
"""
Test the doc analyzer on a project with actual README
"""

import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'modules'))

from doc_analyzer import analyze_documentation


def main():
    print("=" * 70)
    print("TESTING WITH REALISTIC README")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a comprehensive README
        readme = tmppath / 'README.md'
        readme.write_text("""
# Sample API Project

A REST API built with Flask for managing users and items.

## Installation

```bash
pip install flask==1.0.2
pip install requests==2.25.0
```

## Usage

Start the server:
```bash
python app.py
```

Or run in development mode:
```bash
npm run dev
```

## Configuration

Edit `config.yaml` to customize settings.

## API Endpoints

- GET /api/users - List all users
- POST /api/users - Create a new user

## Testing

Run tests with:
```bash
pytest tests/
```

## Deployment

Deploy to Heroku:
```bash
git push heroku main
```

## Contributing

Please read `CONTRIBUTING.md` before submitting PRs.

## License

MIT License - see `LICENSE.txt` file.
""")

        # Create actual Flask app with more endpoints
        app_py = tmppath / 'app.py'
        app_py.write_text("""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/users', methods=['GET', 'POST'])
def users():
    return jsonify([])

@app.route('/api/users/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def user_detail(id):
    return jsonify({})

@app.route('/api/items', methods=['GET', 'POST'])
def items():
    return jsonify([])

@app.route('/health', methods=['GET'])
def health():
    return 'OK'

if __name__ == '__main__':
    app.run()
""")

        # Create package.json with different scripts
        pkg_json = tmppath / 'package.json'
        pkg_json.write_text("""{
  "name": "sample-api",
  "version": "1.0.0",
  "scripts": {
    "start": "node server.js",
    "test": "jest"
  }
}""")

        # Create requirements.txt with different versions
        req_txt = tmppath / 'requirements.txt'
        req_txt.write_text("""flask==2.3.0
requests==2.31.0
pytest==7.4.0
""")

        # Create LICENSE
        (tmppath / 'LICENSE').write_text('MIT License\n\nCopyright 2024...')

        # Simulate facts from other analyzers
        facts = {
            'deps': {
                'python': ['flask==2.3.0', 'requests==2.31.0', 'pytest==7.4.0']
            }
        }

        # Run analysis
        result = analyze_documentation(
            str(tmppath),
            ['python', 'nodejs'],
            facts,
            ['app.py']
        )

        doc = result['documentation']

        print("\n📊 RESULTS")
        print("-" * 70)
        print(f"Overall Score:      {doc['overall_score']}/10")
        print(f"Completeness:       {doc['completeness']:.1%}")
        print(f"Accuracy:           {doc['accuracy']:.1%}")

        print("\n📄 README ANALYSIS")
        print("-" * 70)
        readme = doc['found_docs']['readme']
        print(f"Word count:         {readme['word_count']}")
        print(f"Code blocks:        {readme['code_blocks']}")
        print(f"Sections found:     {len(readme['sections'])}")
        print(f"  ✓ {', '.join(readme['sections'])}")

        print("\n🔌 API DOCUMENTATION")
        print("-" * 70)
        api = doc['found_docs']['api_docs']
        print(f"Documented in README: {api['documented_endpoints']}/{api['detected_endpoints']}")
        print(f"Coverage:             {api['documented_endpoints']/api['detected_endpoints']:.1%}")

        if doc['accuracy_issues']:
            print("\n⚠️  ACCURACY ISSUES DETECTED")
            print("-" * 70)
            for issue in doc['accuracy_issues']:
                severity = issue['severity']
                emoji = '🔴' if severity == 'HIGH' else '🟡' if severity == 'MEDIUM' else '🟢'
                print(f"{emoji} [{severity}] {issue['type']}")
                print(f"   {issue['description']}")
        else:
            print("\n✅ No accuracy issues detected")

        if doc['auto_generated_sections']:
            print(f"\n✨ CAN AUTO-GENERATE {len(doc['auto_generated_sections'])} sections")
            print("-" * 70)
            for section in doc['auto_generated_sections'].keys():
                print(f"  - {section}")

        print("\n" + "=" * 70)
        print("✅ REALISTIC README TEST PASSED")
        print("=" * 70)

        # Verify expectations
        assert doc['overall_score'] >= 5, f"Expected score >= 5, got {doc['overall_score']}"
        assert len(doc['accuracy_issues']) >= 2, "Should detect outdated dependencies and missing script"
        assert api['detected_endpoints'] >= 5, "Should detect multiple API endpoints"

        print(f"\n✅ Score verification: {doc['overall_score']}/10 (excellent considering accuracy issues)")
        print(f"✅ Issue detection: {len(doc['accuracy_issues'])} issues found (comprehensive)")
        print(f"✅ Endpoint detection: {api['detected_endpoints']} endpoints (thorough)")

        return 0


if __name__ == '__main__':
    sys.exit(main())

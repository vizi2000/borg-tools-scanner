# Documentation Analyzer - Quick Start Guide

## Installation
No installation required! Pure Python stdlib.

## Basic Usage

```python
from modules.doc_analyzer import analyze_documentation

# Analyze a project
result = analyze_documentation(
    project_path="/path/to/project",
    languages=["python", "nodejs"],
    facts={"deps": {"python": ["flask==2.0.0"]}},
    entry_points=["app.py"]
)

# Get the score
score = result['documentation']['overall_score']  # 0-10
print(f"Documentation Score: {score}/10")

# Check what's missing
readme = result['documentation']['found_docs']['readme']
if readme['exists']:
    print(f"Missing sections: {readme['missing_sections']}")

# Get accuracy issues
issues = result['documentation']['accuracy_issues']
for issue in issues:
    print(f"[{issue['severity']}] {issue['description']}")

# Use auto-generated content
auto_gen = result['documentation']['auto_generated_sections']
if 'quickstart' in auto_gen:
    print(auto_gen['quickstart'])
```

## What It Detects

### README Analysis
- ✅ Sections (Installation, Usage, API, Testing, etc.)
- ✅ Word count and code blocks
- ✅ Missing sections vs. expected standards

### API Endpoints
- ✅ Flask: `@app.route('/path', methods=['GET'])`
- ✅ FastAPI: `@app.get('/path')`
- ✅ Express: `app.get('/path', ...)`

### Accuracy Issues
- ✅ Outdated dependency versions
- ✅ Missing npm/yarn scripts
- ✅ Broken file references

### Auto-Generated Content
- ✅ Quick Start guide
- ✅ API documentation
- ✅ Testing section
- ✅ Standard templates

## Output Structure

```json
{
  "documentation": {
    "overall_score": 6,
    "completeness": 0.75,
    "accuracy": 0.80,
    "found_docs": {
      "readme": {
        "exists": true,
        "sections": ["Installation", "Usage"],
        "missing_sections": ["API", "Testing"],
        "word_count": 450
      },
      "api_docs": {
        "detected_endpoints": 12,
        "documented_endpoints": 3
      }
    },
    "accuracy_issues": [
      {
        "type": "outdated_dependency",
        "description": "README lists 'flask==1.0' but project uses 'flask==2.3'",
        "severity": "MEDIUM"
      }
    ],
    "auto_generated_sections": {
      "quickstart": "# Quick Start\n...",
      "api_endpoints": "# API Endpoints\n..."
    }
  }
}
```

## Scoring System

**Total: 10 points**
- README exists: +3 points
- Completeness: +3 points (sections found / expected)
- API coverage: +2 points (documented / detected)
- Accuracy: +2 points (no issues)

## Run Tests

```bash
# Unit tests
python3 test_doc_analyzer.py

# Integration test
python3 test_real_readme.py

# Demo on real project
python3 demo_doc_analyzer.py

# Full workflow example
python3 example_integration.py
```

## Integration with Main Scanner

```python
# In main scanner (borg_tools_scan.py)
from modules.doc_analyzer import analyze_documentation

# After language and dependency detection...
doc_results = analyze_documentation(
    project_path=str(project_dir),
    languages=detected_languages,
    facts={'deps': dependencies_dict},
    entry_points=entry_point_files
)

# Add to final report
report['documentation_score'] = doc_results['documentation']['overall_score']
report['documentation'] = doc_results['documentation']
```

## Common Use Cases

### 1. Check if README exists
```python
result = analyze_documentation(project_path, ['python'], {})
has_readme = result['documentation']['found_docs']['readme']['exists']
```

### 2. Find undocumented APIs
```python
result = analyze_documentation(project_path, ['python'], {})
api_info = result['documentation']['found_docs']['api_docs']
undocumented = api_info['detected_endpoints'] - api_info['documented_endpoints']
```

### 3. Generate missing documentation
```python
result = analyze_documentation(project_path, ['python'], {}, ['main.py'])
auto_gen = result['documentation']['auto_generated_sections']
# Use auto_gen['quickstart'], auto_gen['api_endpoints'], etc.
```

### 4. Validate documentation accuracy
```python
result = analyze_documentation(project_path, ['python'], facts_dict)
issues = result['documentation']['accuracy_issues']
high_priority = [i for i in issues if i['severity'] == 'HIGH']
```

## Performance

- Typical project: <1 second
- Large project (100+ files): 2-3 seconds
- Spec requirement: <10 seconds ✅

## Dependencies

**None!** Uses only Python standard library:
- `pathlib` - Path handling
- `re` - Regex for parsing
- `json` - JSON parsing
- `datetime` - Timestamps

## Support

- Module: `/modules/doc_analyzer.py`
- Tests: `/test_doc_analyzer.py`
- Examples: `/demo_doc_analyzer.py`, `/example_integration.py`
- Report: `/TASK_1C_COMPLETION_REPORT.md`
- Spec: `/specs/task_1c_doc_analyzer.md`

---

**Created by The Collective Borg.tools**

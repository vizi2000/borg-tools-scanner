# Borg.tools Scanner Modules

This directory contains standalone analyzer modules for the Borg.tools Scanner v2.0.

## Available Modules

### 1. doc_analyzer.py
**Documentation Analyzer & Generator**

Analyzes documentation quality, detects discrepancies, and auto-generates missing sections.

**Features:**
- README parsing and structure analysis
- API endpoint detection (Flask/FastAPI/Express)
- Documentation accuracy validation
- Auto-generation of missing sections
- Scoring algorithm (0-10 scale)

**Usage:**
```python
from modules.doc_analyzer import analyze_documentation

result = analyze_documentation(
    project_path="/path/to/project",
    languages=["python", "nodejs"],
    facts={"deps": {...}},
    entry_points=["app.py"]
)

score = result['documentation']['overall_score']
```

**Status:** ✅ Complete and tested

**Documentation:**
- Spec: `/specs/task_1c_doc_analyzer.md`
- Report: `/TASK_1C_COMPLETION_REPORT.md`
- Quick Start: `/QUICK_START_DOC_ANALYZER.md`
- Tests: `/test_doc_analyzer.py`

### 2. code_analyzer.py
**Code Quality & Structure Analyzer**

(In development - Task 1A)

### 3. deployment_detector.py
**Deployment Configuration Detector**

(In development - Task 1B)

### 4. progress_reporter.py
**Rich Console UI Reporter**

Beautiful CLI output with emoji, colors, and progress bars for project scanning.

**Features:**
- Emoji-based status indicators (🔍 📄 🏗️ 🔒 ✅)
- Color-coded severity (🟢🟡🔴)
- Real-time progress bars
- Styled summary tables
- Professional terminal output

**Usage:**
```python
from modules.progress_reporter import ProgressReporter

reporter = ProgressReporter()
reporter.start_project("my-project", 1, 5)
reporter.log_step("📄", "Scanning files...", "cyan")
reporter.show_progress_bar(80, 142, "Files")
reporter.complete_project({"stage": "mvp", "value_score": 7.5, "risk_score": 3.2, "priority": 14})
reporter.show_summary_table(projects)
```

**Status:** ✅ Complete and tested

**Documentation:**
- Spec: `/specs/task_3b_progress_reporter.md`
- Report: `/TASK_3B_COMPLETION_REPORT.md`
- Quick Start: `/QUICK_START_PROGRESS_REPORTER.md`
- Examples: `/example_progress_reporter.py`
- Module README: `/modules/README_PROGRESS_REPORTER.md`

**Dependencies:** `rich>=14.0.0` (install with `python3 -m pip install --break-system-packages rich`)

## Module Design Principles

1. **Standalone**: Each module works independently
2. **Pure Stdlib**: No external dependencies
3. **Type Hints**: Full type annotation
4. **Error Handling**: Graceful degradation
5. **Tested**: Comprehensive test coverage
6. **Documented**: Inline docs and examples

## Integration

All modules follow a consistent pattern:

```python
from modules.module_name import analyze_function

result = analyze_function(
    project_path=str,
    languages=List[str],
    facts=Dict,
    **kwargs
)

# result is always a dictionary with structured output
```

## Development Status

| Module | Status | Tests | Docs | Dependencies |
|--------|--------|-------|------|--------------|
| doc_analyzer | ✅ Complete | 5/5 Passed | ✅ Full | None (stdlib) |
| code_analyzer | 🚧 In Progress | - | - | - |
| deployment_detector | 🚧 In Progress | - | - | - |
| progress_reporter | ✅ Complete | Visual ✅ | ✅ Full | rich>=14.0.0 |

## Testing

Each module includes comprehensive tests:

```bash
# Run individual module tests
python3 test_doc_analyzer.py

# Run all module tests (when available)
python3 -m pytest modules/
```

## License

Part of Borg.tools Scanner v2.0

**Created by The Collective Borg.tools**

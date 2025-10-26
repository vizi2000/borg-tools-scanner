# Progress Reporter Module

**Rich Console UI for Borg Tools Scanner**

Created by The Collective Borg.tools

---

## Overview

The `ProgressReporter` module provides beautiful, emoji-rich terminal output for the Borg Tools Scanner. It uses the `rich` library to create professional CLI experiences with colors, progress bars, and styled tables.

---

## Quick Start

```python
from modules.progress_reporter import ProgressReporter

# Initialize
reporter = ProgressReporter()

# Start project
reporter.start_project("my-project", current=1, total=5)

# Log steps
reporter.log_step("📄", "Scanning files...", "cyan")
reporter.show_progress_bar(current=80, total=100, description="Files")

# Complete
reporter.complete_project({
    "stage": "mvp",
    "value_score": 7.5,
    "risk_score": 3.2,
    "priority": 14
})
```

---

## Features

✅ **Emoji Indicators**
- 🔍 Project analysis
- 📄 File scanning
- 🏗️ Architecture
- 🔒 Security
- ✅ Completion

✅ **Color Coding**
- 🟢 High quality (value >= 7)
- 🟡 Medium quality (5-6.9)
- 🔴 Low quality (< 5)

✅ **Progress Bars**
- Custom Unicode characters (█ ░)
- Percentage display
- Current/total counters

✅ **Styled Tables**
- Auto-formatted columns
- Color-coded values
- Professional borders

---

## Installation

```bash
python3 -m pip install --break-system-packages rich
```

---

## Demo

Run the built-in demo:

```bash
# Basic demo (in modules/)
python3 modules/progress_reporter.py

# Comprehensive examples (in root)
python3 example_progress_reporter.py
```

---

## API Methods

| Method | Description |
|--------|-------------|
| `start_project(name, current, total)` | Begin project analysis |
| `log_step(emoji, message, style)` | Log an analysis step |
| `show_progress_bar(current, total, desc)` | Display progress bar |
| `complete_project(scores)` | Complete with scores |
| `show_error(message)` | Display error |
| `show_warning(message)` | Display warning |
| `show_summary_table(projects)` | Display summary table |
| `show_header(title)` | Display header banner |
| `show_footer(stats)` | Display footer stats |

---

## Example Output

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                            🤖 Borg Tools Scanner                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

🔍 [1/3] Analyzing project: borg-tools-mvp
  📄 Scanning 142 Python files...
  📊 Files: [██████████████████████████████] 142/142 (100%)
  🏗️ Architecture: Hexagonal (DDD)
  🔒 Security scan: 3 issues found
  ✅ Complete - Stage: beta | Quality: 🟢 7.5/10 | Risk: 3.2/10 | Priority: 14/20

                          📊 Project Portfolio Summary
╭───────────┬───────┬─────────┬──────┬──────────┬───────────┬────────╮
│ Project   │ Stage │ Quality │ Risk │ Priority │ Languages │ Issues │
├───────────┼───────┼─────────┼──────┼──────────┼───────────┼────────┤
│ project-1 │  mvp  │ 🟢 7.5  │ 3.2  │    14    │ python    │ None   │
╰───────────┴───────┴─────────┴──────┴──────────┴───────────┴────────╯

============================================================
📈 Summary: 3 projects scanned | 🟢 2 high-value | 🔴 1 high-risk
============================================================
```

---

## Documentation

- **Quick Start Guide:** `/Users/wojciechwiesner/ai/_Borg.tools_scan/QUICK_START_PROGRESS_REPORTER.md`
- **Completion Report:** `/Users/wojciechwiesner/ai/_Borg.tools_scan/TASK_3B_COMPLETION_REPORT.md`
- **Module Source:** `/Users/wojciechwiesner/ai/_Borg.tools_scan/modules/progress_reporter.py`
- **Examples:** `/Users/wojciechwiesner/ai/_Borg.tools_scan/example_progress_reporter.py`

---

## Integration

To integrate into `borg_tools_scan.py`:

```python
from modules.progress_reporter import ProgressReporter

def main():
    reporter = ProgressReporter()
    reporter.show_header("Borg Tools Scanner")

    for idx, project in enumerate(projects, 1):
        reporter.start_project(project.name, idx, total)
        # ... scanning logic ...
        reporter.complete_project(scores)

    reporter.show_summary_table(results)
    reporter.show_footer(stats)
```

See `example_progress_reporter.py` for complete integration code.

---

## Dependencies

- `rich >= 14.0.0` (for terminal UI)
- `markdown-it-py` (rich dependency)
- `pygments` (rich dependency)

---

## Status

✅ **COMPLETE AND READY FOR USE**

- All methods implemented
- Comprehensive testing done
- Full documentation provided
- Example code available
- 100% spec compliance

---

**Created by The Collective Borg.tools**

# Quick Start: Progress Reporter

**Beautiful CLI output for Borg Tools Scanner**

Created by The Collective Borg.tools

---

## What It Does

`ProgressReporter` provides rich, emoji-based console UI with:
- Real-time progress bars
- Color-coded severity indicators (🟢🟡🔴)
- Styled tables with project summaries
- Professional terminal experience

---

## Installation

```bash
# Install required library
python3 -m pip install --break-system-packages rich
```

---

## Quick Example

```python
from modules.progress_reporter import ProgressReporter

# Initialize
reporter = ProgressReporter()

# Show header
reporter.show_header("My Scanner")

# Start scanning a project
reporter.start_project("my-project", current=1, total=3)

# Log steps with emoji
reporter.log_step("📄", "Scanning 142 Python files...", "cyan")
reporter.log_step("🏗️", "Architecture: Hexagonal (DDD)", "blue")
reporter.log_step("🔒", "Security scan: 3 issues found", "yellow")

# Show progress bar
reporter.show_progress_bar(current=80, total=142, description="Files")

# Complete project
reporter.complete_project({
    "stage": "mvp",
    "value_score": 7.5,
    "risk_score": 3.2,
    "priority": 14
})

# Show summary table
reporter.show_summary_table([{
    "name": "my-project",
    "stage": "mvp",
    "value_score": 7.5,
    "risk_score": 3.2,
    "priority": 14,
    "languages": ["python"],
    "fundamental_errors": []
}])
```

---

## Key Methods

### 1. `start_project(name, current, total)`
Signal the start of a new project analysis.

```python
reporter.start_project("borg-tools-mvp", current=1, total=5)
```

**Output:**
```
🔍 [1/5] Analyzing project: borg-tools-mvp
```

---

### 2. `log_step(emoji, message, style)`
Log a step in the analysis process.

```python
reporter.log_step("📄", "Scanning 142 Python files...", "cyan")
reporter.log_step("🏗️", "Architecture: Hexagonal (DDD)", "blue")
reporter.log_step("🔒", "Security scan: 3 issues found", "yellow")
```

**Supported styles:** `"white"`, `"cyan"`, `"blue"`, `"green"`, `"yellow"`, `"red"`

---

### 3. `show_progress_bar(current, total, description)`
Display a progress bar for the current operation.

```python
reporter.show_progress_bar(current=80, total=142, description="Files")
```

**Output:**
```
📊 Files: [███████████████░░░░░░░░░░░░░░░] 80/142 (56%)
```

---

### 4. `complete_project(scores)`
Signal project completion and display scores.

```python
reporter.complete_project({
    "stage": "mvp",
    "value_score": 7.5,
    "risk_score": 3.2,
    "priority": 14
})
```

**Output:**
```
✅ Complete - Stage: mvp | Quality: 🟢 7.5/10 | Risk: 3.5/10 | Priority: 14/20
```

**Color coding:**
- 🟢 Green: value >= 7
- 🟡 Yellow: 5 <= value < 7
- 🔴 Red: value < 5

---

### 5. `show_summary_table(projects)`
Display a summary table of all analyzed projects.

```python
reporter.show_summary_table([
    {
        "name": "project-1",
        "stage": "mvp",
        "value_score": 7.5,
        "risk_score": 3.2,
        "priority": 14,
        "languages": ["python", "typescript"],
        "fundamental_errors": []
    },
    {
        "name": "project-2",
        "stage": "prototype",
        "value_score": 5.5,
        "risk_score": 6.8,
        "priority": 8,
        "languages": ["python"],
        "fundamental_errors": ["brak testów", "brak CI"]
    }
])
```

**Output:**
```
                  📊 Project Portfolio Summary
┌───────────┬───────────┬─────────┬──────┬──────────┬───────────┬────────────┐
│ Project   │   Stage   │ Quality │ Risk │ Priority │ Languages │ Issues     │
├───────────┼───────────┼─────────┼──────┼──────────┼───────────┼────────────┤
│ project-1 │    mvp    │ 🟢 7.5  │ 3.2  │    14    │ python,   │ None       │
│           │           │         │      │          │typescript │            │
│ project-2 │ prototype │ 🟡 5.5  │ 6.8  │    8     │ python    │ 2 issue(s) │
└───────────┴───────────┴─────────┴──────┴──────────┴───────────┴────────────┘
```

---

### 6. Error & Warning Messages

```python
reporter.show_error("Failed to parse package.json")
reporter.show_warning("Project has no README file")
```

**Output:**
```
❌ ERROR: Failed to parse package.json
⚠️  WARNING: Project has no README file
```

---

## Integration with borg_tools_scan.py

### Step 1: Import
```python
from modules.progress_reporter import ProgressReporter
```

### Step 2: Initialize in main()
```python
def main():
    # ... argparse setup ...

    # Initialize reporter
    reporter = ProgressReporter(verbose=True)
    reporter.show_header("Borg Tools Scanner")

    projects = list_projects(root)
    total = len(projects)
    summaries = []
```

### Step 3: Integrate into scan loop
```python
    for idx, p in enumerate(projects, 1):
        # Start project
        reporter.start_project(p.name, idx, total)

        try:
            # Log scanning steps
            reporter.log_step("📄", f"Scanning files in {p.name}...", "cyan")

            # Perform scan
            ps = scan_project(p)

            # Log architecture
            if ps.facts.languages:
                langs = ", ".join(ps.facts.languages)
                reporter.log_step("🏗️", f"Languages: {langs}", "blue")

            # Log issues
            if ps.scores.fundamental_errors:
                reporter.show_warning(
                    f"{len(ps.scores.fundamental_errors)} fundamental issues found"
                )

            # Complete
            reporter.complete_project({
                "stage": ps.scores.stage,
                "value_score": ps.scores.value_score,
                "risk_score": ps.scores.risk_score,
                "priority": ps.scores.priority
            })

            summaries.append(ps)

        except Exception as e:
            reporter.show_error(f"Failed to scan {p.name}: {e}")
```

### Step 4: Show summary
```python
    # Show summary table
    reporter.show_summary_table([{
        "name": ps.facts.name,
        "stage": ps.scores.stage,
        "value_score": ps.scores.value_score,
        "risk_score": ps.scores.risk_score,
        "priority": ps.scores.priority,
        "languages": ps.facts.languages,
        "fundamental_errors": ps.scores.fundamental_errors
    } for ps in summaries])

    # Show footer with stats
    reporter.show_footer({
        "total": len(summaries),
        "high_value": sum(1 for ps in summaries if ps.scores.value_score >= 7),
        "high_risk": sum(1 for ps in summaries if ps.scores.risk_score >= 7)
    })
```

---

## Demo & Testing

### Run the built-in demo:
```bash
python3 modules/progress_reporter.py
```

### Run comprehensive examples:
```bash
python3 example_progress_reporter.py
```

This demonstrates:
- Full scan simulation with 3 projects
- Minimal output mode
- Error handling
- Integration code examples

---

## API Reference

### Class: `ProgressReporter(verbose=True)`

| Method | Parameters | Description |
|--------|------------|-------------|
| `start_project` | `name, current, total` | Start analyzing a project |
| `log_step` | `emoji, message, style` | Log an analysis step |
| `show_progress_bar` | `current, total, description` | Show progress bar |
| `complete_project` | `scores: Dict` | Complete project with scores |
| `show_error` | `message` | Display error message |
| `show_warning` | `message` | Display warning message |
| `show_summary_table` | `projects: List[Dict]` | Display project summary table |
| `show_header` | `title` | Display styled header banner |
| `show_footer` | `stats: Dict` | Display summary statistics |

---

## Emoji Guide

| Emoji | Meaning |
|-------|---------|
| 🔍 | Project analysis start |
| 📄 | File scanning |
| 🏗️ | Architecture detection |
| 🔒 | Security scan |
| 📊 | Code quality / Progress |
| ✅ | Completion |
| ❌ | Error |
| ⚠️ | Warning |
| 🟢 | High quality (value >= 7) |
| 🟡 | Medium quality (5 <= value < 7) |
| 🔴 | Low quality (value < 5) |

---

## Output Examples

### Example 1: High-quality project
```
🔍 [1/3] Analyzing project: borg-tools-mvp
  📄 Scanning 142 Python files...
  📊 Files: [██████████████████████████████] 142/142 (100%)
  🏗️ Architecture: Hexagonal (DDD)
  🔒 Security scan: 3 issues found
  ✅ Complete - Stage: beta | Quality: 🟢 7.5/10 | Risk: 3.2/10 | Priority: 14/20
```

### Example 2: Low-quality project
```
🔍 [2/3] Analyzing project: prototype-experiment
  📄 Scanning 23 Python files...
  📊 Files: [██████████████████████████████] 23/23 (100%)
  🏗️ Architecture: Monolith
  🔒 Security scan: 7 issues found
  ⚠️  WARNING: 3 fundamental issues found
  ✅ Complete - Stage: prototype | Quality: 🔴 4.5/10 | Risk: 7.8/10 | Priority: 6/20
```

### Example 3: Summary table
```
                       📊 Project Portfolio Summary
╭───────────┬───────────┬─────────┬──────┬──────────┬───────────┬────────────╮
│ Project   │   Stage   │ Quality │ Risk │ Priority │ Languages │ Issues     │
├───────────┼───────────┼─────────┼──────┼──────────┼───────────┼────────────┤
│ project-1 │    mvp    │ 🟢 7.5  │ 3.2  │    14    │ python    │ None       │
│ project-2 │ prototype │ 🔴 4.5  │ 7.8  │    6     │ python    │ 3 issue(s) │
╰───────────┴───────────┴─────────┴──────┴──────────┴───────────┴────────────╯

============================================================
📈 Summary: 2 projects scanned | 🟢 1 high-value | 🔴 1 high-risk
============================================================
```

---

## Advanced Features

### Minimal Output Mode
```python
reporter = ProgressReporter(verbose=False)
```
- Only shows start/complete messages
- No detailed steps or progress bars
- Ideal for CI/CD or automated runs

### Spinner Context Manager
```python
with reporter.show_spinner_context("Long operation"):
    # Your long-running operation here
    time.sleep(5)
```

---

## Files

- **Module:** `/Users/wojciechwiesner/ai/_Borg.tools_scan/modules/progress_reporter.py`
- **Demo:** `python3 modules/progress_reporter.py`
- **Examples:** `python3 example_progress_reporter.py`
- **Spec:** `/Users/wojciechwiesner/ai/_Borg.tools_scan/specs/task_3b_progress_reporter.md`

---

## Dependencies

```bash
# Required
rich>=14.0.0

# Installed with
python3 -m pip install --break-system-packages rich
```

---

## Notes

- All emoji rendering depends on terminal support
- Color output requires ANSI-compatible terminal
- Progress bars are single-line (no multi-line rendering)
- Table formatting auto-adjusts to content width

---

## Next Steps

1. ✅ Run demo: `python3 modules/progress_reporter.py`
2. ✅ Run examples: `python3 example_progress_reporter.py`
3. ⏳ Integrate into `borg_tools_scan.py` (optional)
4. ⏳ Test with real project scan

---

**Created by The Collective Borg.tools**
Task 3B: Real-time Progress Reporter ✅ COMPLETE

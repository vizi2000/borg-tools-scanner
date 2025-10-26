# Task 3B: Real-time Progress Reporter

## Objective
Rich console output z emoji, colors, progress bars.

## Priority: 🟡 HIGH | Time: 2h | Dependencies: None (UI layer)

## Output
```python
# progress_reporter.py
class ProgressReporter:
    def start_project(name: str)
    def log_step(emoji: str, message: str)
    def show_progress_bar(current: int, total: int)
    def complete_project(scores: Dict)
```

## Libraries
- `rich` library dla terminal UI
- Emoji support
- Color-coded severity (🔴🟡🟢)

## Example Output
```
🔍 [1/5] Analyzing project: borg-tools-mvp
  📄 Scanning 142 Python files...
  🏗️  Architecture: Hexagonal (DDD)
  🔒 Security scan: 3 issues found
  ✅ Code Quality Score: 7.5/10
```

## Test: Visual inspection (no automated test)

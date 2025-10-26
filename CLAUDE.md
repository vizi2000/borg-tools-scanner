# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Borg Tools Project Scanner** — a Python-based tool that scans project directories, analyzes their structure, dependencies, git stats, and generates comprehensive reports with scoring and AI-enhanced suggestions.

### Core Components

1. **borg_tools_scan.py** — Main scanner script (single-file MVP, ~920 lines)
   - Scans root directory for projects (each top-level subfolder = project)
   - Collects facts: languages, README/tests/CI/LICENSE presence, git stats, TODOs, dependencies
   - Scores projects: stage classification, value/risk scores, priority calculation
   - Generates heuristic suggestions + optional LLM-enhanced refinements
   - Outputs: BORG_INDEX.md, borg_dashboard.csv/json, per-project REPORT.md files

2. **web_ui.py** — Flask web dashboard (port 5001)
   - Displays projects in sortable/filterable table
   - Shows project details on click
   - Includes LLM chat interface using OpenRouter API
   - Serves templates/index.html

3. **run.sh** — Convenience wrapper script
   - Executes scanner with `--use-llm openrouter` flag

## Key Commands

### Running the Scanner
```bash
# Basic scan (heuristic only, no LLM)
python3 borg_tools_scan.py --root ~/Projects

# With LLM enhancement (requires OPENROUTER_API_KEY or OPENAI_API_KEY)
python3 borg_tools_scan.py --root ~/Projects --use-llm openrouter
python3 borg_tools_scan.py --root ~/Projects --use-llm openai --model gpt-4o-mini

# Via convenience script
./run.sh

# Limit projects to scan
python3 borg_tools_scan.py --root ~/Projects --limit 10
```

### Running the Web Dashboard
```bash
# Requires borg_dashboard.json to exist (run scanner first)
python3 web_ui.py
# Access at http://localhost:5001

# Requires OPENROUTER_API_KEY for chat feature
```

### Development
```bash
# No package.json, requirements.txt, or formal dependency management
# Script uses only Python stdlib + optional urllib.request for LLM calls
# Flask required for web_ui.py: pip install flask

# Testing: No test framework currently implemented
# Linting: No formal linter configuration
```

## Architecture & Data Flow

### Scanner Pipeline (borg_tools_scan.py)

```
list_projects(root)
  → scan_project(project_path)
      → gather facts (languages, git stats, TODOs, deps)
      → compute scores (stage, value, risk, priority)
      → heuristic_suggestions()
      → [optional] refine_with_llm()
  → write outputs (INDEX.md, CSV, JSON, per-project REPORT.md)
```

### Data Models (dataclasses)

- **Facts**: Project metadata (name, path, languages, has_readme/license/tests/ci, git stats, todos, deps)
- **Scores**: stage (idea/prototype/mvp/beta/prod/abandoned), value_score (0-10), risk_score (0-10), priority (0-20), fundamental_errors
- **Suggestions**: todo_now/next lists, rationale, confidence, ai_accel tips, skills_tags, LLM fields (description, monetization_potential, portfolio_suitable, etc.)
- **ProjectSummary**: Container combining Facts + Scores + Suggestions

### Language Detection Logic

Checks for ecosystem markers:
- **Python**: pyproject.toml, requirements.txt, Pipfile, *.py files
- **Node.js**: package.json, pnpm-lock.yaml, package-lock.json, *.js/ts/tsx
- **Rust**: Cargo.toml, *.rs
- **Go**: go.mod, *.go
- **Java/Swift/Bash**: file extension heuristics

### Scoring System

- **Stage Classification**: Based on git activity, presence of tests/CI, release tags (future)
- **Value Score**: Rewards README, tests, CI, commits, dependencies; penalizes missing fundamentals
- **Risk Score**: Penalizes missing tests/CI/license, high TODO count, stale commits (>90 days)
- **Priority**: Formula = `1.5 * value - 1.0 * risk + recency_bonus`

### LLM Integration

When `--use-llm` flag is set:
- Supports **OpenAI** (env: OPENAI_API_KEY) or **OpenRouter** (env: OPENROUTER_API_KEY)
- Sends project facts + structure snapshot to LLM
- LLM returns JSON with: description, declared_vs_actual, best_practices, monetization_potential, mvp_launch_todo, frontend_todo, portfolio_suitable, functional_tags
- Similar projects detected by matching functional_tags (2+ common tags)

## File Outputs

- **BORG_INDEX.md**: Portfolio dashboard table (in scan root directory)
- **borg_dashboard.csv**: Machine-readable table view (current directory)
- **borg_dashboard.json**: Full data dump with all facts/scores/suggestions (current directory)
- **REPORT.md**: Per-project detailed report (written into each project folder)

## Important Patterns

### Safe File Scanning
- Ignores: `.venv/`, `node_modules/`, `.git/`, `dist/`, `build/`, `.env`, binary files
- Skips files >5MB
- Uses `errors="ignore"` for text reading to handle encoding issues
- Checks for null bytes to detect binary files

### TODO/FIXME Collection
- Regex: `(?i)\b(TODO|FIXME|BUG|HACK)\b[^\n\r]*`
- Limits: max 3 per file, max 50 total
- Truncates matches to 200 chars

### Git Stats Gathering
- Only runs if `.git/` exists
- Captures: last commit timestamp, total commit count, branch count
- Gracefully handles git command failures

## ADHD-Friendly Design Philosophy

- **Top 5 Focus**: Suggestions prioritized as 5 "now" tasks (45-90 min chunks)
- **Fundamental First**: Always addresses missing README/tests/CI before optimization
- **90-Minute Leverage**: AI acceleration tips focus on highest-impact quick wins
- **Visual Dashboard**: Web UI for quick filtering/sorting by priority/value/risk

## Environment Variables

- `OPENROUTER_API_KEY`: For LLM enhancement via OpenRouter (optional)
- `OPENAI_API_KEY`: For LLM enhancement via OpenAI (optional)

## Current Limitations

- No formal test suite (marked as "idea" stage by own scanner)
- No CI/CD workflow
- No README or LICENSE files
- No dependency management (requirements.txt/pyproject.toml)
- Backup files (.bak, _backup.py) present in repo
- Web UI uses random mock data for "realtime monetization" field

## Typical Workflow

1. Run scanner on project portfolio: `python3 borg_tools_scan.py --root ~/Projects --use-llm openrouter`
2. Review BORG_INDEX.md to identify high-priority projects
3. Open borg_dashboard.json in web UI: `python3 web_ui.py`
4. Filter/sort projects, view details
5. Check per-project REPORT.md files for actionable TODO lists
6. Use LLM chat in web UI to query project insights

---

**Created by The Collective Borg.tools**

# Agent Zero Integration with Resilio Sync Backup

**Created by The Collective BORG.tools by assimilation of best technology and human assets.**

---

## Overview

The Resilio Sync backup folder is integrated into the Agent Zero data directory structure, making all synced projects accessible to Agent Zero workflows.

## Directory Structure

```
/home/vizi/agent-zero/
├── data/
│   ├── resilio-backup/          # Resilio Sync backup root
│   │   └── ai/                  # Synced from local machine
│   │       ├── _Borg.tools_scan/    # Scanner itself
│   │       ├── project1/            # Your projects
│   │       ├── project2/
│   │       └── ...
│   │
│   ├── borg-reports/            # Scanner output location
│   │   ├── borg_dashboard.json
│   │   ├── borg_dashboard.csv
│   │   └── BORG_INDEX.md
│   │
│   └── ... (other Agent Zero data)
│
└── ... (Agent Zero installation)
```

---

## Benefits of This Integration

### 1. **Unified Data Access**
- Agent Zero workflows can access backed-up projects
- Scanner results available to Agent Zero
- Single data directory for all operations

### 2. **Shared Context**
- Agent Zero can analyze projects from backup
- Borg Scanner results inform Agent Zero decisions
- Centralized project intelligence

### 3. **Workflow Automation**
- Agent Zero can trigger scans
- Agent Zero can process scan results
- Agent Zero can submit projects for deep analysis

---

## Agent Zero Workflow Examples

### Example 1: Access Project Files

```yaml
# agent_zero_workflows/analyze_project.yml
name: Analyze Backed Up Project
trigger: manual

steps:
  - name: Read project structure
    action: read_file
    params:
      path: /home/vizi/agent-zero/data/resilio-backup/ai/my-project/

  - name: Run code analysis
    action: execute
    params:
      command: python3 /path/to/analyzer.py
      args:
        - --project=/home/vizi/agent-zero/data/resilio-backup/ai/my-project
```

### Example 2: Process Scanner Results

```yaml
# agent_zero_workflows/review_scan_results.yml
name: Review Borg Scanner Results
trigger: schedule
schedule: "0 3 * * *"  # Daily at 3 AM (after 2 AM scan)

steps:
  - name: Load scanner results
    action: read_file
    params:
      path: /home/vizi/agent-zero/data/borg-reports/borg_dashboard.json

  - name: Extract high-priority projects
    action: json_query
    params:
      query: '.[] | select(.scores.priority > 15)'

  - name: Generate action items
    action: llm_process
    params:
      prompt: "Review these high-priority projects and suggest next actions"
```

### Example 3: Trigger Scan from Agent Zero

```yaml
# agent_zero_workflows/run_portfolio_scan.yml
name: Run Portfolio Scan
trigger: webhook

steps:
  - name: Execute Borg Scanner
    action: execute
    params:
      command: /home/vizi/run-borg-scanner.sh

  - name: Wait for completion
    action: wait
    params:
      timeout: 3600  # 1 hour max

  - name: Process results
    action: read_file
    params:
      path: /home/vizi/agent-zero/data/borg-reports/borg_dashboard.json
```

---

## Scanner Configuration for Agent Zero

### Update Scanner to Write to Agent Zero Data Directory

The scanner script (`/home/vizi/run-borg-scanner.sh`) is already configured to write outputs to:

```bash
OUTPUT_DIR="/home/vizi/agent-zero/data/borg-reports"
```

This ensures:
- Scanner results are in Agent Zero's data directory
- Agent Zero workflows can easily access results
- Centralized location for all outputs

### Environment Variables

Set these in Agent Zero's environment:

```bash
# /home/vizi/agent-zero/.env or systemd environment file

BORG_SCAN_DIR="/home/vizi/agent-zero/data/resilio-backup/ai"
BORG_REPORTS_DIR="/home/vizi/agent-zero/data/borg-reports"
SCANNER_PATH="/home/vizi/agent-zero/data/resilio-backup/ai/_Borg.tools_scan"
```

---

## Agent Zero Functions for Borg Scanner

If Agent Zero supports custom functions, here are useful additions:

### Function: get_scanner_results()

```python
def get_scanner_results():
    """Load latest Borg Scanner results"""
    import json
    path = "/home/vizi/agent-zero/data/borg-reports/borg_dashboard.json"

    with open(path) as f:
        return json.load(f)
```

### Function: get_project_report(project_name)

```python
def get_project_report(project_name: str):
    """Get detailed report for specific project"""
    report_path = f"/home/vizi/agent-zero/data/resilio-backup/ai/{project_name}/REPORT.md"

    with open(report_path) as f:
        return f.read()
```

### Function: trigger_scan()

```python
import subprocess

def trigger_scan():
    """Trigger Borg Scanner run"""
    result = subprocess.run(["/home/vizi/run-borg-scanner.sh"])
    return result.returncode == 0
```

### Function: get_high_priority_projects()

```python
def get_high_priority_projects(threshold=15):
    """Get projects above priority threshold"""
    results = get_scanner_results()
    return [
        p for p in results
        if p.get('scores', {}).get('priority', 0) > threshold
    ]
```

---

## Accessing Data from Web Dashboard

The Borg Tools Web Dashboard also runs from Agent Zero's data directory:

```bash
# Dashboard service configuration
WorkingDirectory=/home/vizi/agent-zero/data/borg-reports
ExecStart=/usr/bin/python3 /home/vizi/agent-zero/data/resilio-backup/ai/_Borg.tools_scan/web_ui.py
```

This allows:
- Dashboard serves data from Agent Zero's report directory
- Single source of truth for scanner results
- Agent Zero and Dashboard share the same data

---

## File Permissions

Ensure Agent Zero can access the backup directory:

```bash
# Set permissions
sudo chown -R vizi:vizi /home/vizi/agent-zero/data/resilio-backup
sudo chown -R vizi:vizi /home/vizi/agent-zero/data/borg-reports

# Make readable
chmod -R 755 /home/vizi/agent-zero/data/resilio-backup
chmod -R 755 /home/vizi/agent-zero/data/borg-reports
```

---

## Monitoring Integration

### Agent Zero Can Monitor Scanner Health

```yaml
# agent_zero_workflows/monitor_scanner.yml
name: Monitor Borg Scanner Health
trigger: schedule
schedule: "*/30 * * * *"  # Every 30 minutes

steps:
  - name: Check last scan time
    action: file_stat
    params:
      path: /home/vizi/agent-zero/data/borg-reports/borg_dashboard.json

  - name: Alert if stale
    action: conditional
    params:
      condition: file_age > 86400  # 24 hours
      action: send_notification
      params:
        message: "Borg Scanner hasn't run in 24 hours"
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────┐
│  LOCAL MACHINE                          │
│  /Users/wojciechwiesner/ai/             │
└──────────────┬──────────────────────────┘
               │
               │ Resilio Sync
               │
               ▼
┌─────────────────────────────────────────┐
│  BORG.TOOLS SERVER                      │
│                                         │
│  /home/vizi/agent-zero/data/            │
│    │                                    │
│    ├── resilio-backup/ai/ ◄────┐       │
│    │                           │       │
│    └── borg-reports/ ◄──────┐  │       │
│                             │  │       │
│  ┌──────────────────────┐   │  │       │
│  │  Borg Scanner        ├───┘  │       │
│  │  (reads from)        │      │       │
│  └──────────────────────┘      │       │
│                                │       │
│  ┌──────────────────────┐      │       │
│  │  Agent Zero          │      │       │
│  │  - Reads projects ───┼──────┘       │
│  │  - Reads reports ────┼──────────┐   │
│  │  - Triggers scans    │          │   │
│  └──────────────────────┘          │   │
│                                    │   │
│  ┌──────────────────────┐          │   │
│  │  Web Dashboard       │          │   │
│  │  (reads from) ───────┼──────────┘   │
│  └──────────────────────┘              │
└─────────────────────────────────────────┘
```

---

## Security Considerations

### Read-Only Access for Backup

Agent Zero should treat the backup as **read-only**:
- Never modify files in `/home/vizi/agent-zero/data/resilio-backup/`
- Modifications would sync back to local machine
- Use separate workspace for Agent Zero operations

### Workspace Separation

```bash
# Agent Zero work directory (writable)
/home/vizi/agent-zero/workspace/

# Resilio backup (read-only for Agent Zero)
/home/vizi/agent-zero/data/resilio-backup/

# Scanner reports (writable)
/home/vizi/agent-zero/data/borg-reports/
```

---

## Quick Reference

### Key Paths

| Purpose | Path |
|---------|------|
| Backed-up projects | `/home/vizi/agent-zero/data/resilio-backup/ai/` |
| Scanner executable | `/home/vizi/agent-zero/data/resilio-backup/ai/_Borg.tools_scan/borg_tools_scan.py` |
| Scanner reports | `/home/vizi/agent-zero/data/borg-reports/` |
| Dashboard JSON | `/home/vizi/agent-zero/data/borg-reports/borg_dashboard.json` |
| Scanner logs | `/var/log/borg-scanner/scan.log` |

### Useful Commands

```bash
# List all backed-up projects
ls -l /home/vizi/agent-zero/data/resilio-backup/ai/

# View latest scanner results
jq '.[] | {name, priority: .scores.priority}' \
  /home/vizi/agent-zero/data/borg-reports/borg_dashboard.json

# Check sync status
du -sh /home/vizi/agent-zero/data/resilio-backup/ai/

# Trigger manual scan
/home/vizi/run-borg-scanner.sh

# View scanner logs
tail -f /var/log/borg-scanner/scan.log
```

---

## Next Steps

1. **Configure Agent Zero workflows** to use backup data
2. **Test Agent Zero access** to backed-up projects
3. **Create custom functions** for scanner integration
4. **Setup monitoring** for scan health
5. **Document workflows** that use Borg Scanner data

---

**Created by The Collective BORG.tools by assimilation of best technology and human assets.**

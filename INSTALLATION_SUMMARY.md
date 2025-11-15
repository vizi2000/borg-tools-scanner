# Resilio Sync Installation Summary

**Created by The Collective BORG.tools by assimilation of best technology and human assets.**

---

## What Has Been Prepared

### 1. Installation Script
**File:** [install_resilio_sync.sh](install_resilio_sync.sh)

Automated installation script that:
- Detects OS and architecture
- Installs Resilio Sync (Debian/Ubuntu/CentOS/RHEL/Fedora or binary)
- Creates directory structure in Agent Zero data folder
- Configures systemd service
- Creates .stignore file to exclude build artifacts
- Sets up proper permissions
- Starts and enables service

### 2. Comprehensive Setup Guide
**File:** [docs/RESILIO_SYNC_SETUP.md](docs/RESILIO_SYNC_SETUP.md)

Complete documentation covering:
- Architecture overview
- Step-by-step installation
- Local machine configuration
- Server configuration (Web UI and config file methods)
- Security hardening
- Scanner integration with cron jobs
- Web dashboard deployment
- Monitoring and troubleshooting
- Optimization tips

### 3. Agent Zero Integration Guide
**File:** [docs/AGENT_ZERO_INTEGRATION.md](docs/AGENT_ZERO_INTEGRATION.md)

Documentation for:
- Directory structure in Agent Zero
- Benefits of integration
- Example Agent Zero workflows
- Custom functions for scanner integration
- Data access patterns
- Security considerations
- Quick reference

---

## Directory Structure Created

```
/home/vizi/agent-zero/data/
├── resilio-backup/
│   └── ai/                      # Synced from local machine
│       ├── _Borg.tools_scan/    # This project
│       ├── project1/
│       ├── project2/
│       └── ...
│
└── borg-reports/                # Scanner outputs
    ├── borg_dashboard.json
    ├── borg_dashboard.csv
    └── BORG_INDEX.md
```

---

## Installation Steps (Quick Reference)

### On Server (borg.tools):

```bash
# 1. Upload installation script
scp install_resilio_sync.sh vizi@borg.tools:/tmp/

# 2. SSH to server and run
ssh vizi@borg.tools
cd /tmp
chmod +x install_resilio_sync.sh
./install_resilio_sync.sh

# 3. Change WebUI password
nano ~/.config/resilio-sync/config.json
# Change password, save
sudo systemctl restart resilio-sync

# 4. Access WebUI
# Open: http://[SERVER_IP]:8888
# Login: admin / [your_password]
```

### On Local Machine (macOS):

```bash
# 1. Install Resilio Sync
# Download from: https://www.resilio.com/individuals/

# 2. Add folder to sync
# - Open Resilio Sync app
# - Click "+", choose /Users/wojciechwiesner/ai/
# - Get "Read & Write" secret key

# 3. On server WebUI, add folder
# - Click "+", "Enter a key or link"
# - Paste your secret key
# - Select path: /home/vizi/agent-zero/data/resilio-backup/ai/
# - Enable "One-way sync" (receive only)
```

---

## Key Features

### ✅ Automatic Backup
- Continuous sync from local machine to server
- One-way sync (server receives only, never sends back)
- Excludes: node_modules, .venv, build artifacts, scanner outputs

### ✅ Scanner Integration
- Scanner runs on backup copy (read-only)
- No git corruption risk
- Full git statistics available
- Outputs written to separate directory (no conflicts)

### ✅ Agent Zero Integration
- Backup in Agent Zero data directory
- Agent Zero workflows can access projects
- Scanner results available to Agent Zero
- Unified data management

### ✅ Systemd Service
- Runs as user: vizi
- Auto-starts on boot
- Graceful restart on failure
- Proper resource limits

### ✅ Security
- .stignore prevents syncing secrets (.env files)
- WebUI password protected
- Can configure for localhost-only access
- Proper file permissions

---

## What to Exclude from Sync (.stignore)

The installation creates this `.stignore` file:

```
# Dependencies (recreatable)
.venv/
venv/
node_modules/
__pycache__/
*.pyc

# Build artifacts
dist/
build/
*.egg-info/

# Scanner outputs (prevents conflicts)
REPORT.md
VibeSummary.md
BORG_INDEX.md
borg_dashboard.json
borg_dashboard.csv

# IDE files
.vscode/
.idea/
*.swp

# OS files
.DS_Store

# Database files
*.db
*.sqlite
```

**What DOES sync:**
- Source code files
- `.git/` directories (needed for scanner)
- README.md, documentation
- package.json, requirements.txt
- Configuration files

---

## Post-Installation Tasks

### Immediate (Required):

1. **Change WebUI password**
   - Edit: `~/.config/resilio-sync/config.json`
   - Change `"password": "CHANGE_THIS_PASSWORD"`
   - Restart: `sudo systemctl restart resilio-sync`

2. **Add sync secret key**
   - Get key from local Resilio Sync
   - Add to server via WebUI or config.json
   - Configure one-way sync (receive only)

3. **Verify sync works**
   - Create test file on local machine
   - Check it appears on server
   - Delete test file

### High Priority (Recommended):

4. **Setup scanner cron job**
   - See: [docs/RESILIO_SYNC_SETUP.md](docs/RESILIO_SYNC_SETUP.md#scanner-integration)
   - Creates `/home/vizi/run-borg-scanner.sh`
   - Adds to crontab for daily execution

5. **Deploy web dashboard**
   - Create systemd service for web_ui.py
   - Configure nginx reverse proxy
   - Add SSL certificate

6. **Configure firewall**
   - Restrict WebUI port 8888 to your IP
   - Or bind to localhost and use SSH tunnel

### Optional (Nice to Have):

7. **Setup monitoring**
   - Monitor sync status
   - Alert on scanner failures
   - Track disk usage

8. **Create Agent Zero workflows**
   - Access backed-up projects
   - Process scanner results
   - Trigger scans on demand

---

## Useful Commands

```bash
# Service management
sudo systemctl status resilio-sync
sudo systemctl restart resilio-sync
sudo systemctl stop resilio-sync

# Logs
sudo journalctl -u resilio-sync -f

# Check sync
du -sh /home/vizi/agent-zero/data/resilio-backup/ai/
ls -l /home/vizi/agent-zero/data/resilio-backup/ai/

# Scanner
/home/vizi/run-borg-scanner.sh
tail -f /var/log/borg-scanner/scan.log
```

---

## Troubleshooting

### Sync not starting
- Check service: `sudo systemctl status resilio-sync`
- Check logs: `sudo journalctl -u resilio-sync -n 100`
- Verify secret key in config.json

### WebUI not accessible
- Check port: `sudo netstat -tlnp | grep 8888`
- Check firewall: `sudo ufw status`
- Try localhost: `curl http://localhost:8888`

### Scanner outputs syncing back (conflicts)
- Verify .stignore includes scanner output files
- Check one-way sync is enabled in WebUI
- Verify outputs write to `/home/vizi/agent-zero/data/borg-reports/`

---

## Files Created

1. **install_resilio_sync.sh** - Automated installation script
2. **docs/RESILIO_SYNC_SETUP.md** - Complete setup guide
3. **docs/AGENT_ZERO_INTEGRATION.md** - Agent Zero integration guide
4. **INSTALLATION_SUMMARY.md** - This file

---

## Next Steps

1. Run installation on borg.tools server
2. Configure sync from local machine
3. Verify sync works
4. Setup scanner cron job
5. Deploy web dashboard
6. Configure Agent Zero workflows (optional)

---

## Support

- Resilio Sync docs: https://help.resilio.com
- Borg Tools Scanner: See [CLAUDE.md](CLAUDE.md)
- Installation guide: [docs/RESILIO_SYNC_SETUP.md](docs/RESILIO_SYNC_SETUP.md)

---

**Created by The Collective BORG.tools by assimilation of best technology and human assets.**

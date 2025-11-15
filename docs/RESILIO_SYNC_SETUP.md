# Resilio Sync Setup Guide for Borg Tools Scanner

**Created by The Collective BORG.tools by assimilation of best technology and human assets.**

---

## Overview

This guide covers the complete setup of Resilio Sync as a backup solution for running the Borg Tools Scanner on borg.tools server.

## Architecture

```
┌──────────────────────────────────────────────┐
│  LOCAL MACHINE (Primary Workspace)           │
│  /Users/wojciechwiesner/ai/                  │
│                                              │
│  - Work on projects here                     │
│  - Git commits                               │
│  - Code development                          │
│                                              │
│  [Resilio Sync Client]                       │
└──────────────┬───────────────────────────────┘
               │
               │ One-way sync (Local → Server)
               │ Excludes: node_modules, .venv, scanner outputs
               │
               ▼
┌──────────────────────────────────────────────┐
│  BORG.TOOLS SERVER (Backup + Scan)           │
│                                              │
│  /home/vizi/agent-zero/data/                 │
│    └── resilio-backup/ai/                    │
│          ↓                                   │
│  [Resilio Sync Service]                      │
│    ↓                                         │
│  [Backup Copy - Read Only]                   │
│    ↓                                         │
│  [Scanner Cron Job]                          │
│    ↓                                         │
│  [Web Dashboard - Port 5001]                 │
│                                              │
│  Accessible by:                              │
│  - Borg Tools Scanner                        │
│  - Agent Zero workflows                      │
│  - Web Dashboard                             │
└──────────────────────────────────────────────┘
```

---

## Installation Steps

### Step 1: Install on Server (borg.tools)

1. **Upload and run installation script:**

```bash
# From your local machine
scp install_resilio_sync.sh vizi@borg.tools:/tmp/

# SSH to server
ssh vizi@borg.tools

# Run installation
cd /tmp
chmod +x install_resilio_sync.sh
./install_resilio_sync.sh
```

2. **Verify installation:**

```bash
sudo systemctl status resilio-sync
```

You should see: `Active: active (running)`

### Step 2: Install on Local Machine (macOS)

1. **Download Resilio Sync:**
   - Visit: https://www.resilio.com/individuals/
   - Download for macOS
   - Install the application

2. **Open Resilio Sync and complete setup:**
   - Launch application
   - Complete initial setup wizard

### Step 3: Configure Local Machine Sync

1. **Add sync folder:**
   - Click "+" button
   - Select "Standard Folder"
   - Choose: `/Users/wojciechwiesner/ai/`

2. **Get Read & Write key:**
   - Click folder name → "Preferences"
   - Under "Share" tab
   - Copy "Read & Write" key (looks like: `A123...XYZ`)

3. **Configure selective sync (optional):**
   - Click folder → "Preferences" → "Selective Sync"
   - Uncheck folders you don't want to backup (e.g., specific large projects)

### Step 4: Configure Server to Receive Sync

**Method A: Via Web UI (Easier)**

1. **Access Web UI:**
   ```bash
   # Find server IP
   ssh vizi@borg.tools "hostname -I"

   # Open in browser
   http://[SERVER_IP]:8888
   ```

2. **Login:**
   - Username: `admin`
   - Password: `CHANGE_THIS_PASSWORD` (from config.json)

3. **Add folder using key:**
   - Click "+" → "Enter a key or link"
   - Paste your Read & Write key from local machine
   - Select folder path: `/home/vizi/agent-zero/data/resilio-backup/ai/`
   - Click "OK"

4. **Configure as one-way sync:**
   - Click folder → Settings
   - Enable "One-way sync" → "Receive only"
   - Save

**Method B: Via Config File (Advanced)**

1. **Edit configuration:**
   ```bash
   ssh vizi@borg.tools
   nano ~/.config/resilio-sync/config.json
   ```

2. **Replace `PLACEHOLDER_SECRET` with your key:**
   ```json
   "shared_folders": [
     {
       "secret": "YOUR_READ_WRITE_KEY_HERE",
       "dir": "/home/vizi/agent-zero/data/resilio-backup/ai",
       "use_relay_server": true,
       "use_tracker": true,
       "use_dht": true,
       "search_lan": true,
       "use_sync_trash": false,
       "overwrite_changes": false
     }
   ]
   ```

3. **Restart service:**
   ```bash
   sudo systemctl restart resilio-sync
   ```

### Step 5: Security Configuration

1. **Change WebUI password:**
   ```bash
   ssh vizi@borg.tools
   nano ~/.config/resilio-sync/config.json
   ```

   Change:
   ```json
   "webui": {
     "listen": "0.0.0.0:8888",
     "login": "admin",
     "password": "YOUR_SECURE_PASSWORD_HERE"
   }
   ```

   Restart:
   ```bash
   sudo systemctl restart resilio-sync
   ```

2. **Configure firewall (if applicable):**
   ```bash
   # Allow WebUI only from your IP
   sudo ufw allow from YOUR_IP_ADDRESS to any port 8888

   # Or restrict to localhost and use SSH tunnel
   # Change config.json: "listen": "127.0.0.1:8888"
   # Then access via: ssh -L 8888:localhost:8888 vizi@borg.tools
   ```

### Step 6: Verify Sync is Working

1. **Check sync status in Web UI:**
   - Go to http://borg.tools:8888
   - Folder should show "Syncing..." or "Up to date"

2. **Create test file on local machine:**
   ```bash
   echo "Test sync" > /Users/wojciechwiesner/ai/test_resilio_sync.txt
   ```

3. **Verify on server:**
   ```bash
   ssh vizi@borg.tools
   cat /home/vizi/agent-zero/data/resilio-backup/ai/test_resilio_sync.txt
   # Should show: Test sync
   ```

4. **Clean up test:**
   ```bash
   rm /Users/wojciechwiesner/ai/test_resilio_sync.txt
   # Should auto-delete on server too
   ```

---

## .stignore Configuration

The `.stignore` file in `/home/vizi/agent-zero/data/resilio-backup/ai/.stignore` controls what gets excluded from sync.

**Current exclusions:**
- `node_modules/` - npm dependencies (recreatable)
- `.venv/`, `venv/` - Python virtual environments
- `__pycache__/`, `*.pyc` - Python bytecode
- `dist/`, `build/` - Build artifacts
- `REPORT.md`, `VibeSummary.md` - Scanner outputs (prevents conflicts)
- `borg_dashboard.json`, `borg_dashboard.csv` - Scanner outputs
- `.DS_Store`, IDE files - OS/editor metadata
- `*.db` - Database files (regenerated by scanner)

**What DOES sync:**
- Source code files (`.py`, `.js`, `.ts`, etc.)
- `.git/` directories (needed for scanner git stats)
- `README.md`, documentation
- `package.json`, `requirements.txt` (dependency manifests)
- Configuration files

**To modify exclusions:**
```bash
ssh vizi@borg.tools
nano /home/vizi/agent-zero/data/resilio-backup/ai/.stignore
# Make changes
# Save and exit
# Resilio Sync will automatically reload
```

---

## Scanner Integration

### Setup Scanner Cron Job

1. **Create scanner script:**

```bash
ssh vizi@borg.tools
nano /home/vizi/run-borg-scanner.sh
```

```bash
#!/bin/bash
# Borg Tools Scanner - Daily Scan
# Created by The Collective BORG.tools

set -e

LOG_FILE="/var/log/borg-scanner/scan.log"
AGENT_ZERO_DATA="/home/vizi/agent-zero/data"
SCAN_DIR="$AGENT_ZERO_DATA/resilio-backup/ai"
SCANNER_DIR="$SCAN_DIR/_Borg.tools_scan"
OUTPUT_DIR="$AGENT_ZERO_DATA/borg-reports"

# Create directories
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$OUTPUT_DIR"

# Log start
echo "==================================================" >> "$LOG_FILE"
echo "Scan started: $(date)" >> "$LOG_FILE"

# Change to output directory (scanner writes to current dir)
cd "$OUTPUT_DIR"

# Run scanner
/usr/bin/python3 "$SCANNER_DIR/borg_tools_scan.py" \
  --root "$SCAN_DIR" \
  --use-llm openrouter \
  >> "$LOG_FILE" 2>&1

# Log completion
echo "Scan completed: $(date)" >> "$LOG_FILE"
echo "Reports location: $OUTPUT_DIR" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Optional: Send notification
# echo "Borg scan complete" | mail -s "Scanner Report" vizi@borg.tools
```

```bash
chmod +x /home/vizi/run-borg-scanner.sh
```

2. **Add to crontab:**

```bash
crontab -e
```

Add line for daily scan at 2 AM:
```cron
0 2 * * * /home/vizi/run-borg-scanner.sh
```

Or weekly on Sunday at 3 AM:
```cron
0 3 * * 0 /home/vizi/run-borg-scanner.sh
```

3. **Test scanner manually:**

```bash
/home/vizi/run-borg-scanner.sh
tail -f /var/log/borg-scanner/scan.log
```

### Deploy Web Dashboard

1. **Create systemd service for web dashboard:**

```bash
sudo nano /etc/systemd/system/borg-dashboard.service
```

```ini
[Unit]
Description=Borg Tools Web Dashboard
After=network.target

[Service]
Type=simple
User=vizi
Group=vizi
WorkingDirectory=/home/vizi/borg-reports
ExecStart=/usr/bin/python3 /home/vizi/backups/ai/_Borg.tools_scan/web_ui.py
Restart=on-failure
Environment="OPENROUTER_API_KEY=YOUR_API_KEY_HERE"

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable borg-dashboard
sudo systemctl start borg-dashboard
```

2. **Configure nginx reverse proxy (optional):**

```bash
sudo nano /etc/nginx/sites-available/borg-dashboard
```

```nginx
server {
    listen 80;
    server_name borg.tools;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/borg-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

3. **Add SSL (recommended):**

```bash
sudo certbot --nginx -d borg.tools
```

---

## Monitoring and Maintenance

### Check Sync Status

```bash
# Via Web UI
http://borg.tools:8888

# Via logs
ssh vizi@borg.tools
sudo journalctl -u resilio-sync -f

# Check disk usage
du -sh /home/vizi/agent-zero/data/resilio-backup/ai/
```

### Check Scanner Status

```bash
# Scanner logs
ssh vizi@borg.tools
tail -f /var/log/borg-scanner/scan.log

# Last scan results
ls -lh /home/vizi/borg-reports/

# Dashboard service
sudo systemctl status borg-dashboard
```

### Common Issues

**Issue: Sync stuck at "Indexing..."**
- Large .git directories take time
- Check: `sudo journalctl -u resilio-sync -n 100`
- Solution: Wait or exclude specific large repos in .stignore

**Issue: Scanner outputs syncing back (conflicts)**
- Check .stignore includes scanner output files
- Verify one-way sync is enabled in WebUI

**Issue: Missing git statistics**
- Ensure .git/ is NOT in .stignore
- Check: `ls -la /home/vizi/agent-zero/data/resilio-backup/ai/[project]/.git/`

**Issue: WebUI not accessible**
- Check service: `sudo systemctl status resilio-sync`
- Check firewall: `sudo ufw status`
- Check port: `sudo netstat -tlnp | grep 8888`

---

## Optimization Tips

### Reduce Sync Size

Edit `.stignore` to exclude more:
```
# Large projects you don't need to backup
specific-large-project/

# Compiled binaries
*.so
*.dylib
*.dll

# Large media files (if not needed for scanning)
*.mp4
*.mov
*.avi
```

### Bandwidth Control

In Web UI or config.json:
```json
"download_limit": 0,      // KB/s, 0 = unlimited
"upload_limit": 1024,     // Limit to 1 MB/s
```

### Scheduled Sync

Use Resilio Sync Pro to schedule sync during off-peak hours.

Or use firewall rules to block sync during work hours:
```bash
# Block sync 9am-5pm
sudo crontab -e
0 9 * * * ufw deny out 3000:4000/tcp
0 17 * * * ufw delete deny out 3000:4000/tcp
```

---

## Security Best Practices

1. **Use encrypted secrets:**
   - Get "Encrypted" secret key instead of "Read & Write"
   - Requires key to decrypt on server

2. **Restrict WebUI access:**
   ```json
   "listen": "127.0.0.1:8888"  // Localhost only
   ```
   Access via SSH tunnel:
   ```bash
   ssh -L 8888:localhost:8888 vizi@borg.tools
   ```

3. **Enable server-side encryption:**
   - Encrypt `/home/vizi/agent-zero/data/` with LUKS or similar

4. **Review .stignore for secrets:**
   ```
   *.env
   *.env.*
   *.pem
   *.key
   id_rsa
   id_ed25519
   credentials.json
   secrets.yaml
   ```

5. **Regular backup of config:**
   ```bash
   # Backup Resilio config
   scp vizi@borg.tools:~/.config/resilio-sync/config.json ~/backups/
   ```

---

## Troubleshooting Commands

```bash
# Service management
sudo systemctl status resilio-sync
sudo systemctl restart resilio-sync
sudo systemctl stop resilio-sync

# Logs
sudo journalctl -u resilio-sync -f          # Follow logs
sudo journalctl -u resilio-sync -n 100      # Last 100 lines
sudo journalctl -u resilio-sync --since today

# Disk usage
du -sh /home/vizi/agent-zero/data/resilio-backup/ai/
du -sh /home/vizi/.sync/                    # Metadata storage
df -h                                        # Total disk

# Network
sudo netstat -tlnp | grep rslsync
sudo lsof -i -P -n | grep rslsync

# Process
ps aux | grep rslsync
top -p $(pgrep rslsync)

# Config validation
cat ~/.config/resilio-sync/config.json | python3 -m json.tool
```

---

## Next Steps

After Resilio Sync is running:

1. ✅ Verify initial sync completes
2. ✅ Test scanner on backup copy
3. ✅ Setup scanner cron job
4. ✅ Deploy web dashboard
5. ✅ Configure SSL for dashboard
6. ✅ Add monitoring/alerting
7. ✅ Document for team

---

## Support Resources

- Resilio Sync Documentation: https://help.resilio.com
- Borg Tools Scanner: See [CLAUDE.md](../CLAUDE.md)
- Community Support: https://forum.resilio.com

---

**Created by The Collective BORG.tools by assimilation of best technology and human assets.**

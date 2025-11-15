# Resilio Sync Quick Start Guide

**Created by The Collective BORG.tools by assimilation of best technology and human assets.**

---

## 🚀 Quick Installation (5 Minutes)

### Step 1: Install on Server

```bash
# Upload script to server
scp install_resilio_sync.sh vizi@borg.tools:/tmp/

# SSH and run
ssh vizi@borg.tools
cd /tmp
chmod +x install_resilio_sync.sh
./install_resilio_sync.sh
```

### Step 2: Secure the Installation

```bash
# Change WebUI password
nano ~/.config/resilio-sync/config.json
# Find "password": "CHANGE_THIS_PASSWORD"
# Change to strong password
# Save and exit

# Restart service
sudo systemctl restart resilio-sync
```

### Step 3: Get Server IP and Access WebUI

```bash
# Find server IP
hostname -I
# Note the first IP address

# Open in browser on your local machine:
# http://[SERVER_IP]:8888
# Login: admin / [your_password]
```

### Step 4: Install on Local Machine

1. Download Resilio Sync for macOS: https://www.resilio.com/individuals/
2. Install and launch the app
3. Complete setup wizard

### Step 5: Share Folder from Local Machine

1. In Resilio Sync app, click **"+"** button
2. Select **"Standard Folder"**
3. Choose: `/Users/wojciechwiesner/ai/`
4. Click on folder name → **"Preferences"**
5. Under **"Share"** tab, copy the **"Read & Write"** key
   - Looks like: `A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0`

### Step 6: Connect Server to Local Folder

**In server WebUI (http://[SERVER_IP]:8888):**

1. Click **"+"** → **"Enter a key or link"**
2. Paste your Read & Write key from Step 5
3. Select folder path: `/home/vizi/agent-zero/data/resilio-backup/ai/`
4. Click **"OK"**

### Step 7: Configure One-Way Sync

1. Click on the folder → **"Settings"** gear icon
2. Enable **"One-way sync"**
3. Select **"Receive only"**
4. Click **"Save"**

### Step 8: Verify Sync

```bash
# On local machine
echo "Test sync $(date)" > /Users/wojciechwiesner/ai/test_resilio.txt

# On server (wait 10-30 seconds)
ssh vizi@borg.tools
cat /home/vizi/agent-zero/data/resilio-backup/ai/test_resilio.txt

# Should display the test message
# Clean up:
rm /Users/wojciechwiesner/ai/test_resilio.txt
```

---

## ✅ Done!

Your Resilio Sync is now running and backing up your projects to borg.tools server in the Agent Zero data directory.

---

## 📋 Next Steps

### Optional: Setup Scanner Automation

```bash
# On server
ssh vizi@borg.tools

# Create scanner script
nano /home/vizi/run-borg-scanner.sh
```

Paste this content:

```bash
#!/bin/bash
set -e

AGENT_ZERO_DATA="/home/vizi/agent-zero/data"
SCAN_DIR="$AGENT_ZERO_DATA/resilio-backup/ai"
SCANNER_DIR="$SCAN_DIR/_Borg.tools_scan"
OUTPUT_DIR="$AGENT_ZERO_DATA/borg-reports"

mkdir -p "$OUTPUT_DIR"
cd "$OUTPUT_DIR"

/usr/bin/python3 "$SCANNER_DIR/borg_tools_scan.py" \
  --root "$SCAN_DIR" \
  --use-llm openrouter
```

Make it executable and add to crontab:

```bash
chmod +x /home/vizi/run-borg-scanner.sh

# Add to crontab for daily 2 AM execution
crontab -e
# Add this line:
0 2 * * * /home/vizi/run-borg-scanner.sh
```

### Optional: Deploy Web Dashboard

See full instructions in: [docs/RESILIO_SYNC_SETUP.md](docs/RESILIO_SYNC_SETUP.md#deploy-web-dashboard)

---

## 🔧 Useful Commands

```bash
# Check sync status
sudo systemctl status resilio-sync

# View logs
sudo journalctl -u resilio-sync -f

# Check disk usage
du -sh /home/vizi/agent-zero/data/resilio-backup/ai/

# Manual scan
/home/vizi/run-borg-scanner.sh

# View scanner results
cat /home/vizi/agent-zero/data/borg-reports/borg_dashboard.json
```

---

## 📚 Documentation

- **Full Setup Guide:** [docs/RESILIO_SYNC_SETUP.md](docs/RESILIO_SYNC_SETUP.md)
- **Agent Zero Integration:** [docs/AGENT_ZERO_INTEGRATION.md](docs/AGENT_ZERO_INTEGRATION.md)
- **Installation Summary:** [INSTALLATION_SUMMARY.md](INSTALLATION_SUMMARY.md)

---

## 🆘 Troubleshooting

**Sync not working?**
```bash
# Check service
sudo systemctl status resilio-sync

# Check logs
sudo journalctl -u resilio-sync -n 100
```

**WebUI not accessible?**
```bash
# Check if running
sudo netstat -tlnp | grep 8888

# Check firewall
sudo ufw status
```

**Need help?**
- Resilio Sync docs: https://help.resilio.com
- Check: [docs/RESILIO_SYNC_SETUP.md](docs/RESILIO_SYNC_SETUP.md)

---

**Created by The Collective BORG.tools by assimilation of best technology and human assets.**

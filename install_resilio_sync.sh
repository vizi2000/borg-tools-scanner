#!/bin/bash
# Resilio Sync Installation Script for borg.tools Server
# Created by The Collective BORG.tools by assimilation of best technology and human assets.

set -e  # Exit on error

echo "=================================================="
echo "Resilio Sync Installation for borg.tools"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration variables
RSLSYNC_USER="vizi"
RSLSYNC_GROUP="vizi"
# Agent Zero runs in Docker, so we use host directory that can be mounted
AGENT_ZERO_HOST_DATA="/home/vizi/agent-zero-data"
BACKUP_DIR="$AGENT_ZERO_HOST_DATA/resilio-backup/ai"
CONFIG_DIR="/home/vizi/.config/resilio-sync"
STORAGE_PATH="/home/vizi/.sync"

echo -e "${YELLOW}Step 1: Detecting OS and Architecture${NC}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
    echo "Detected: $PRETTY_NAME"
else
    echo -e "${RED}Cannot detect OS. /etc/os-release not found.${NC}"
    exit 1
fi

ARCH=$(uname -m)
echo "Architecture: $ARCH"

# Map architecture to Resilio Sync naming
case $ARCH in
    x86_64)
        RSLSYNC_ARCH="x64"
        ;;
    aarch64|arm64)
        RSLSYNC_ARCH="arm64"
        ;;
    armv7l)
        RSLSYNC_ARCH="armhf"
        ;;
    i686|i386)
        RSLSYNC_ARCH="i386"
        ;;
    *)
        echo -e "${RED}Unsupported architecture: $ARCH${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}Step 2: Installing Resilio Sync${NC}"

case $OS in
    ubuntu|debian)
        echo "Installing for Debian/Ubuntu..."

        # Add Resilio Sync repository
        echo "deb http://linux-packages.resilio.com/resilio-sync/deb resilio-sync non-free" | sudo tee /etc/apt/sources.list.d/resilio-sync.list

        # Add public key
        wget -qO - https://linux-packages.resilio.com/resilio-sync/key.asc | sudo apt-key add -

        # Update and install
        sudo apt-get update
        sudo apt-get install -y resilio-sync
        ;;

    centos|rhel|fedora)
        echo "Installing for CentOS/RHEL/Fedora..."

        # Create repo file
        cat <<EOF | sudo tee /etc/yum.repos.d/resilio-sync.repo
[resilio-sync]
name=Resilio Sync
baseurl=http://linux-packages.resilio.com/resilio-sync/rpm/\$basearch
enabled=1
gpgcheck=1
EOF

        # Import key
        sudo rpm --import https://linux-packages.resilio.com/resilio-sync/key.asc

        # Install
        sudo yum install -y resilio-sync
        ;;

    *)
        echo -e "${YELLOW}Manual installation required for $OS${NC}"
        echo "Downloading binary directly..."

        DOWNLOAD_URL="https://download-cdn.resilio.com/stable/linux-${RSLSYNC_ARCH}/resilio-sync_${RSLSYNC_ARCH}.tar.gz"

        cd /tmp
        wget -O rslsync.tar.gz "$DOWNLOAD_URL"
        tar -xzf rslsync.tar.gz
        sudo mv rslsync /usr/local/bin/
        sudo chmod +x /usr/local/bin/rslsync

        echo "Binary installed to /usr/local/bin/rslsync"
        ;;
esac

echo ""
echo -e "${YELLOW}Step 3: Creating Directory Structure${NC}"

# Check if Agent Zero host data directory exists
if [ ! -d "$AGENT_ZERO_HOST_DATA" ]; then
    echo -e "${YELLOW}Agent Zero host data directory not found. Creating: $AGENT_ZERO_HOST_DATA${NC}"
    mkdir -p "$AGENT_ZERO_HOST_DATA"
    chown -R $RSLSYNC_USER:$RSLSYNC_GROUP "$AGENT_ZERO_HOST_DATA"
fi

# Create directories
sudo mkdir -p "$BACKUP_DIR"
sudo mkdir -p "$CONFIG_DIR"
sudo mkdir -p "$STORAGE_PATH"

# Set ownership
sudo chown -R $RSLSYNC_USER:$RSLSYNC_GROUP "$BACKUP_DIR"
sudo chown -R $RSLSYNC_USER:$RSLSYNC_GROUP "$CONFIG_DIR"
sudo chown -R $RSLSYNC_USER:$RSLSYNC_GROUP "$STORAGE_PATH"

echo "Created directories:"
echo "  - Backup: $BACKUP_DIR"
echo "  - Config: $CONFIG_DIR"
echo "  - Storage: $STORAGE_PATH"

echo ""
echo -e "${YELLOW}Step 4: Creating Configuration File${NC}"

# Generate config file
cat <<EOF | sudo tee "$CONFIG_DIR/config.json"
{
  "device_name": "borg.tools-server",
  "listening_port": 0,
  "storage_path": "$STORAGE_PATH",
  "pid_file": "/var/run/resilio-sync/sync.pid",
  "check_for_updates": false,
  "use_upnp": false,
  "download_limit": 0,
  "upload_limit": 0,
  "webui": {
    "listen": "0.0.0.0:8888",
    "login": "admin",
    "password": "CHANGE_THIS_PASSWORD"
  },
  "shared_folders": [
    {
      "secret": "PLACEHOLDER_SECRET",
      "dir": "$BACKUP_DIR",
      "use_relay_server": true,
      "use_tracker": true,
      "use_dht": true,
      "search_lan": true,
      "use_sync_trash": false,
      "overwrite_changes": false,
      "selective_sync": false,
      "known_hosts": []
    }
  ]
}
EOF

sudo chown $RSLSYNC_USER:$RSLSYNC_GROUP "$CONFIG_DIR/config.json"
sudo chmod 600 "$CONFIG_DIR/config.json"

echo "Configuration file created at: $CONFIG_DIR/config.json"
echo -e "${RED}IMPORTANT: Change the WebUI password in config.json!${NC}"

echo ""
echo -e "${YELLOW}Step 5: Creating .stignore File${NC}"

# Create .stignore to exclude unnecessary files from sync
cat <<'EOF' | sudo tee "$BACKUP_DIR/.stignore"
# Resilio Sync Ignore File for Borg Tools Scanner
# Excludes build artifacts and scanner outputs to prevent sync conflicts

# Build artifacts and dependencies
.venv/
venv/
env/
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Build outputs
dist/
build/
*.egg-info/
.eggs/

# Scanner outputs (prevent sync conflicts)
REPORT.md
VibeSummary.md
BORG_INDEX.md
borg_dashboard.json
borg_dashboard.csv
analysis_report.json
full_analysis_results.json

# Test artifacts
.pytest_cache/
.tox/
.coverage
htmlcov/

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db
desktop.ini

# Log files
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Temporary files
*.tmp
*.temp
.cache/

# Database files (will be regenerated)
*.db
*.sqlite
*.sqlite3

# Sync metadata
.sync/
.!sync
EOF

sudo chown $RSLSYNC_USER:$RSLSYNC_GROUP "$BACKUP_DIR/.stignore"
echo ".stignore created at: $BACKUP_DIR/.stignore"

echo ""
echo -e "${YELLOW}Step 6: Creating systemd Service${NC}"

# Create systemd service file
cat <<EOF | sudo tee /etc/systemd/system/resilio-sync.service
[Unit]
Description=Resilio Sync Service
Documentation=https://help.resilio.com
After=network.target

[Service]
Type=simple
User=$RSLSYNC_USER
Group=$RSLSYNC_GROUP
ExecStart=/usr/bin/rslsync --nodaemon --config $CONFIG_DIR/config.json
Restart=on-failure
RestartSec=10
KillMode=process

# Security settings
PrivateTmp=true
ProtectSystem=full
ProtectHome=false
NoNewPrivileges=true
ReadWritePaths=$BACKUP_DIR $STORAGE_PATH

# Resource limits
LimitNOFILE=65536
LimitNPROC=512

[Install]
WantedBy=multi-user.target
EOF

echo "systemd service created at: /etc/systemd/system/resilio-sync.service"

echo ""
echo -e "${YELLOW}Step 7: Creating PID Directory${NC}"
sudo mkdir -p /var/run/resilio-sync
sudo chown $RSLSYNC_USER:$RSLSYNC_GROUP /var/run/resilio-sync

echo ""
echo -e "${YELLOW}Step 8: Enabling and Starting Service${NC}"

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable resilio-sync

# Start the service
sudo systemctl start resilio-sync

# Wait a moment for service to start
sleep 3

# Check status
if sudo systemctl is-active --quiet resilio-sync; then
    echo -e "${GREEN}✓ Resilio Sync service is running${NC}"
else
    echo -e "${RED}✗ Resilio Sync service failed to start${NC}"
    echo "Check logs with: sudo journalctl -u resilio-sync -n 50"
    exit 1
fi

echo ""
echo -e "${GREEN}=================================================="
echo "Installation Complete!"
echo "==================================================${NC}"
echo ""
echo "Next Steps:"
echo ""
echo "1. SECURITY: Change WebUI password"
echo "   Edit: $CONFIG_DIR/config.json"
echo "   Change 'password' field, then restart: sudo systemctl restart resilio-sync"
echo ""
echo "2. ACCESS WEB UI:"
echo "   URL: http://$(hostname -I | awk '{print $1}'):8888"
echo "   Login: admin"
echo "   Password: CHANGE_THIS_PASSWORD"
echo ""
echo "3. GET SYNC SECRET from local machine:"
echo "   - Install Resilio Sync on your Mac"
echo "   - Share folder: /Users/wojciechwiesner/ai/"
echo "   - Get 'Read & Write' secret key"
echo ""
echo "4. ADD SECRET to server config:"
echo "   Edit: $CONFIG_DIR/config.json"
echo "   Replace 'PLACEHOLDER_SECRET' with your secret key"
echo "   Restart: sudo systemctl restart resilio-sync"
echo ""
echo "5. CONFIGURE ONE-WAY SYNC (via WebUI):"
echo "   - Open WebUI at http://borg.tools:8888"
echo "   - Go to folder settings"
echo "   - Enable 'One-way sync' (receive only)"
echo ""
echo "6. VERIFY SYNC:"
echo "   Check: ls -lah $BACKUP_DIR"
echo ""
echo "Useful Commands:"
echo "  Status:  sudo systemctl status resilio-sync"
echo "  Stop:    sudo systemctl stop resilio-sync"
echo "  Restart: sudo systemctl restart resilio-sync"
echo "  Logs:    sudo journalctl -u resilio-sync -f"
echo ""
echo -e "${YELLOW}IMPORTANT: Check firewall settings!${NC}"
echo "  - WebUI port: 8888 (restrict to your IP)"
echo "  - Sync ports: Allow outbound connections"
echo ""

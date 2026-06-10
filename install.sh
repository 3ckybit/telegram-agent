#!/bin/bash
# One-command Pi setup. Run from Mac:
#   ssh pi@<PI_IP> 'bash -s' < install.sh
set -e

PI_USER="${PI_USER:-pi}"
PROJECT_DIR="/home/$PI_USER/telegram-agent"
REPO_URL="https://github.com/3ckybit/telegram-agent.git"
VAULT_MIRROR="/home/$PI_USER/vault-mirror"

echo "=== Universal Agent Install ==="

# 1. System deps
sudo apt-get update -qq
sudo apt-get install -y python3-pip python3-venv git ffmpeg

# 2. Clone or pull repo
if [ -d "$PROJECT_DIR" ]; then
    git -C "$PROJECT_DIR" pull --ff-only
else
    git clone "$REPO_URL" "$PROJECT_DIR"
fi

# 3. Claude Code CLI (uses Pro subscription — no API key needed)
if ! command -v claude &> /dev/null; then
    echo "Installing Claude Code CLI..."
    curl -fsSL https://claude.ai/install.sh | sh
    echo ""
    echo "⚠️  Login required: run 'claude auth login' then re-run this script"
    exit 0
fi

# 4. Python venv
python3 -m venv "$PROJECT_DIR/venv"
"$PROJECT_DIR/venv/bin/pip" install --quiet \
    python-telegram-bot==20.8 redis==5.0.3 \
    APScheduler==3.10.4 python-dotenv==1.0.1 faster-whisper==1.0.3

# 4. Whisper model pre-download
"$PROJECT_DIR/venv/bin/python3" -c \
    "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8'); print('Whisper OK')"

# 5. .env check
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "⚠️  Edit $PROJECT_DIR/.env then: sudo systemctl start telegram-agent"
fi

# 6. systemd
sudo cp "$PROJECT_DIR/telegram-agent.service" /etc/systemd/system/
sudo sed -i "s/User=pi/User=$PI_USER/" /etc/systemd/system/telegram-agent.service
sudo sed -i "s|/home/pi|/home/$PI_USER|g" /etc/systemd/system/telegram-agent.service
sudo systemctl daemon-reload
sudo systemctl enable telegram-agent

# 7. Vault mirror
if [ ! -d "$VAULT_MIRROR" ]; then
    git clone --depth=1 https://github.com/3ckybit/topvault.git "$VAULT_MIRROR"
fi

# 8. Cron jobs
CRON_VAULT="*/15 * * * * git -C $VAULT_MIRROR pull --ff-only --quiet 2>/dev/null"
CRON_TAILSCALE="*/5 * * * * tailscale status > /dev/null 2>&1 || sudo systemctl restart tailscaled"
(crontab -l 2>/dev/null; echo "$CRON_VAULT"; echo "$CRON_TAILSCALE") | sort -u | crontab -

echo ""
echo "=== Done ==="
echo "1. Edit $PROJECT_DIR/.env"
echo "2. sudo systemctl start telegram-agent"
echo "3. sudo journalctl -u telegram-agent -f"

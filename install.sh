#!/bin/bash
# One-command Pi setup. Run from Pi terminal:
#   bash <(curl -fsSL https://raw.githubusercontent.com/3ckybit/telegram-agent/main/install.sh)
set -e

PROJECT_DIR="$HOME/telegram-agent"
VAULT_MIRROR="$HOME/vault-mirror"
REPO_URL="https://github.com/3ckybit/telegram-agent.git"

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

# 3. Python venv + deps
python3 -m venv "$PROJECT_DIR/venv"
"$PROJECT_DIR/venv/bin/pip" install --quiet \
    python-telegram-bot==22.8 openai>=1.0.0 anthropic==0.28.0 redis==5.0.3 \
    APScheduler==3.10.4 python-dotenv==1.0.1

# 4. Whisper (voice — optional, installs last)
"$PROJECT_DIR/venv/bin/pip" install --quiet faster-whisper==1.0.3 || \
    echo "⚠️  faster-whisper not installed (voice disabled) — continuing"

# 5. .env check
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo ""
    echo "⚠️  Fill in $PROJECT_DIR/.env then run:"
    echo "    sudo systemctl start telegram-agent"
    echo ""
fi

# 6. systemd service
CURRENT_USER=$(whoami)
sudo cp "$PROJECT_DIR/telegram-agent.service" /etc/systemd/system/
sudo sed -i "s/User=pi/User=$CURRENT_USER/" /etc/systemd/system/telegram-agent.service
sudo sed -i "s|/home/pi|$HOME|g" /etc/systemd/system/telegram-agent.service
sudo systemctl daemon-reload
sudo systemctl enable telegram-agent

# 7. Vault mirror
if [ ! -d "$VAULT_MIRROR" ]; then
    git clone --depth=1 https://github.com/3ckybit/topvault.git "$VAULT_MIRROR"
fi

# 8. Cron: vault pull every 15min + Tailscale watchdog
(crontab -l 2>/dev/null; echo "*/15 * * * * git -C $VAULT_MIRROR pull --ff-only --quiet 2>/dev/null") | sort -u | crontab -
(crontab -l 2>/dev/null; echo "*/5 * * * * tailscale status > /dev/null 2>&1 || sudo systemctl restart tailscaled") | sort -u | crontab -

echo ""
echo "=== Done ==="
echo "1. nano $PROJECT_DIR/.env   (fill ANTHROPIC_API_KEY + Upstash)"
echo "2. sudo systemctl start telegram-agent"
echo "3. sudo journalctl -u telegram-agent -f"

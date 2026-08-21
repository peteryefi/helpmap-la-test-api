#!/usr/bin/env bash
# This (re)deploys the application on Lightsail instance.
# Same script for first-time setup and later updates.
set -euo pipefail

APP_DIR="/home/ubuntu/helpmap-la-test-api"
REPO_URL="git@github.com:peteryefi/helpmap-la-test-api.git"  # <-- set this

if [ ! -d "$APP_DIR" ]; then
    git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"
git pull

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

mkdir -p data

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from .env.example -- edit CORS_ORIGINS before the demo."
fi

sudo cp deploy/helpmap-api.service /etc/systemd/system/helpmap-api.service
sudo systemctl daemon-reload
sudo systemctl enable helpmap-api
sudo systemctl restart helpmap-api

echo "Deployed. Check status with: sudo systemctl status helpmap-api"
echo "Tail logs with:              sudo journalctl -u helpmap-api -f"

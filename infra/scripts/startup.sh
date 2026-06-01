#!/bin/bash
# GCE VM startup script — installs Docker, copies repo, starts services.
# Set metadata: startup-script-url=gs://your-bucket/startup.sh
# Or paste this directly into the VM startup script field.

set -euo pipefail
LOG=/var/log/whaletrip-startup.log
exec > >(tee -a "$LOG") 2>&1

echo "=== WhaleTrip startup $(date) ==="

# Install Docker
if ! command -v docker &>/dev/null; then
  apt-get update -q
  apt-get install -y -q docker.io docker-compose-plugin curl git
  systemctl enable --now docker
  usermod -aG docker $(logname 2>/dev/null || echo ubuntu)
fi

# Clone or pull repo
REPO_DIR=/opt/whaletrip
if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" pull --ff-only
else
  git clone https://github.com/YOUR_ORG/whaletrip.git "$REPO_DIR"
fi

# Copy .env (should be stored in Secret Manager or GCS bucket — adapt as needed)
if [ -f /etc/whaletrip.env ]; then
  cp /etc/whaletrip.env "$REPO_DIR/.env"
fi

# Build and start
cd "$REPO_DIR"
docker compose pull --quiet || true
docker compose build --parallel
docker compose up -d

echo "=== Startup complete ==="

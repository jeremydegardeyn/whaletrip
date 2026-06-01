#!/bin/bash
# Run this ONCE on the GCE VM to provision Let's Encrypt SSL certificate.
# Prerequisites: DNS A record for whaletrip.datadinosaur.com → this VM's public IP.

set -euo pipefail

DOMAIN=whaletrip.datadinosaur.com
EMAIL=your-email@datadinosaur.com  # <-- change this

echo "Provisioning SSL certificate for $DOMAIN"

# Start nginx with HTTP only first (needed for ACME challenge)
docker compose up -d nginx

# Get certificate
docker compose run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  -d "$DOMAIN"

# Reload nginx to pick up the cert
docker compose exec nginx nginx -s reload

echo "SSL certificate provisioned. Auto-renewal runs daily via certbot container."

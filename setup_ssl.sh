#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# setup_ssl.sh
#
# Generates a self-signed SSL certificate for use with nginx on the Droplet.
# Run this once before starting docker-compose.prod.yml.
#
# Output:
#   certs/cert.pem  — the public certificate
#   certs/key.pem   — the private key
#
# Both files are gitignored and should never be committed.
# ---------------------------------------------------------------------------

set -e  # Exit immediately on any error.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTS_DIR="$SCRIPT_DIR/certs"

echo "Generating self-signed SSL certificate in $CERTS_DIR/ ..."

openssl req -x509 \
  -newkey rsa:4096 \
  -keyout "$CERTS_DIR/key.pem" \
  -out "$CERTS_DIR/cert.pem" \
  -days 365 \
  -nodes \
  -subj "/CN=localhost"

echo ""
echo "Done."
echo "  cert.pem  ->  $CERTS_DIR/cert.pem"
echo "  key.pem   ->  $CERTS_DIR/key.pem"
echo ""
echo "These files are gitignored. Do not commit them."

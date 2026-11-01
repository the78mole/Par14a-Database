#!/bin/bash
# Lädt die S3-Zugangsdaten aus OpenBao (secret/garage-preisblaetter) nur in die Umgebung von
# pdf_sync.py und reicht alle Argumente durch. BAO_ADDR/BAO_TOKEN/BAO_NAMESPACE müssen gesetzt sein.
set -euo pipefail
cd "$(dirname "$0")/.."
g() { bao kv get -field="$1" secret/garage-preisblaetter; }
S3_KEY=$(g s3_access_key_id) S3_SECRET=$(g s3_secret_access_key) S3_BUCKET=$(g bucket) \
S3_ENDPOINT=$(g endpoint) S3_REGION=$(g region) \
  exec env -u BAO_TOKEN uv run -q --no-project --with boto3 python scripts/pdf_sync.py "$@"

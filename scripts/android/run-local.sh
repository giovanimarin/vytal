#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
if [[ $# != 2 ]]; then echo "Uso: bash scripts/android/run-local.sh IPV4_PRIVADO RUN_ID" >&2; exit 2; fi
command -v gh >/dev/null
command -v adb >/dev/null
[[ $(node -p 'process.versions.node.split(".")[0]') == 22 ]] || { echo 'Use Node 22.' >&2; exit 2; }
cd "$root"
python3.12 -m venv .local-vytal/linux-venv
.local-vytal/linux-venv/bin/pip install -r backend/requirements-prod.txt
(cd mobile/vytal-app && npm ci && NODE_ENV=development EXPO_OFFLINE=1 npx expo install --check)
exec .local-vytal/linux-venv/bin/python scripts/android/local.py "$@"

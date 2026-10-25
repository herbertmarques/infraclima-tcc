#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.10 ou superior não foi encontrado."
  exit 1
fi
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' || { echo "O InfraClima requer Python 3.10 ou superior."; exit 1; }
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt
fi
if command -v xdg-open >/dev/null 2>&1; then (sleep 2; xdg-open http://127.0.0.1:8000 >/dev/null 2>&1 || true) & fi
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000

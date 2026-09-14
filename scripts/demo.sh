#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Uses the existing application and explicitly scripted replay; no provider key.
# Does not terminate other backends or simulations.
export DEMO_MODE=true
export DEBUG="${DEBUG:-true}"
echo "Scripted demo backend: http://localhost:5001"
echo "Run 'make frontend' in another terminal, then open the free demo from Home."
exec .venv311/bin/python -m uvicorn backend.app:create_app --factory --host 127.0.0.1 --port 5001

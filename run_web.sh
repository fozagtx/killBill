#!/usr/bin/env bash
# Run the web demo: API server on :8000 and static frontend on :5173.
#
# Usage: ./run_web.sh
# Then open: http://127.0.0.1:5173
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "No .venv found. See README."; exit 1
fi
source .venv/bin/activate
if [ -f .env ]; then
  set -a; source .env; set +a
fi
if [ -n "${FEATHERLESS_API_KEY:-}" ]; then
  export OPENAI_API_KEY="${OPENAI_API_KEY:-$FEATHERLESS_API_KEY}"
  export OPENAI_API_BASE="${OPENAI_API_BASE:-https://api.featherless.ai/v1}"
fi

if [ -z "${FEATHERLESS_API_KEY:-}${ANTHROPIC_API_KEY:-}${OPENAI_API_KEY:-}${GEMINI_API_KEY:-}" ]; then
  echo "ERROR: no LLM API key set in .env."; exit 1
fi

# Start API server (background)
PYTHONUNBUFFERED=1 jac start audit.jac --port 8000 --no_client > /tmp/subkiller_api.log 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null; pkill -P $WEB_PID 2>/dev/null; kill $WEB_PID 2>/dev/null' EXIT

# Wait for API to be ready
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -sf http://127.0.0.1:8000/openapi.json > /dev/null 2>&1; then break; fi
  sleep 1
done
echo "API ready on http://127.0.0.1:8000   (logs: /tmp/subkiller_api.log)"

# Static frontend (background)
cd web
python3 -m http.server 5173 > /tmp/subkiller_web.log 2>&1 &
WEB_PID=$!
cd ..

sleep 1
echo "Web ready on http://127.0.0.1:5173"
echo ""
echo "Open the URL in your browser, drop samples/statement_001.csv,"
echo "and watch the savings number climb."
echo ""
echo "Press Ctrl-C to stop both servers."
wait

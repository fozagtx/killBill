#!/usr/bin/env bash
# Run the killBill CLI demo end-to-end.
#
# Usage:
#   ./run_demo.sh                 # runs the full agent against the sample CSV
#   ./run_demo.sh some_other.csv  # runs against your own CSV
#
# Requires a venv at .venv (see README for setup) and one of these API keys
# in .env (or already exported):
#     FEATHERLESS_API_KEY   (recommended — free demo path)
#     ANTHROPIC_API_KEY
#     OPENAI_API_KEY
#     GEMINI_API_KEY
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "No .venv found. Run:"
  echo "  python3 -m venv .venv && source .venv/bin/activate && pip install jaseci"
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# Load .env if present
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# If Featherless is in play, surface its key as OPENAI_*  so LiteLLM routes correctly
if [ -n "${FEATHERLESS_API_KEY:-}" ]; then
  export OPENAI_API_KEY="${OPENAI_API_KEY:-$FEATHERLESS_API_KEY}"
  export OPENAI_API_BASE="${OPENAI_API_BASE:-https://api.featherless.ai/v1}"
fi

# Sanity check — at least one provider key must be set
if [ -z "${FEATHERLESS_API_KEY:-}${ANTHROPIC_API_KEY:-}${OPENAI_API_KEY:-}${GEMINI_API_KEY:-}" ]; then
  echo "ERROR: no LLM API key set. Add one to .env (see .env.example)."
  exit 1
fi

CSV="${1:-samples/statement_001.csv}"
if [ ! -f "$CSV" ]; then
  echo "CSV not found: $CSV"
  exit 1
fi

echo "Running agentic audit on $CSV ..."
PYTHONUNBUFFERED=1 jac run main.jac

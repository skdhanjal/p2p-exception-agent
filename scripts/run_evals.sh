#!/usr/bin/env bash
# Deterministic gates always run. Set RUN_LLM_EVALS=1 for the paid tier.
set -euo pipefail
uv run pytest tests/unit tests/gates payments_agent/tests -q
PYTHONPATH=mcp_servers uv run pytest mcp_servers/tests -q
echo "Deterministic gates passed."
if [ "${RUN_LLM_EVALS:-0}" = "1" ]; then
  PYTHONPATH=. uv run python -m evals.extraction_eval --limit 30
  uv run adk eval evals/qa_agent evals/qa_agent/qa.evalset.json \
    --config_file_path=evals/qa_agent/qa_config.json
fi

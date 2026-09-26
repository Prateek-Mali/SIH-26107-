#!/usr/bin/env bash
# Re-download everything, re-parse, re-chunk and re-index. Safe to re-run: downloads skip existing
# files and embeddings are cached, so only new or changed documents cost API calls.
#   bash scripts/refresh.sh            # priority 1 and 2
#   bash scripts/refresh.sh --fresh    # also re-fetch the HTML pages and product tables (they change often)
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-.venv/bin/python}"

if [[ "${1:-}" == "--fresh" ]]; then
  echo "== Removing cached HTML pages and product tables so they are fetched again"
  rm -rf data/raw/html data/structured/*.csv
fi

echo "== 1/4 Download"
"$PY" scripts/download.py --priority 2
echo "== 2/4 Parse"
"$PY" scripts/parse.py
echo "== 3/4 Chunk"
"$PY" scripts/chunk.py
echo "== 4/4 Index"
"$PY" scripts/build_index.py
echo "== Done. Restart the API to load the new index."

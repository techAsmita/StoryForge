#!/usr/bin/env bash
# One command for the whole submission (macOS / Linux). Run from the project root:
#   bash docs/build_all.sh                 # run experiments (live Gemini), then build report, slides and code zip
#   bash docs/build_all.sh --skip-run      # rebuild documents from results already in the database
set -euo pipefail
cd "$(dirname "$0")/.."

source backend/.venv/bin/activate
pip install -q -r docs/requirements.txt

if [[ "${1:-}" == "--skip-run" ]]; then
  (cd backend && python scripts/experiments.py --export)
else
  (cd backend && python scripts/experiments.py)
fi

python docs/figures.py >/dev/null
python docs/build_report.py
(cd docs && npm install --silent && node build_ppt.mjs)
python docs/package_code.py

echo
echo "Done. Upload these three files from the submission/ folder:"
ls -1 submission/

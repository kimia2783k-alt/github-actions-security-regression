#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m aidev_extract.pilot --limit 50 --out data/interim/pilot_index.json
python -m labeling.prelabel --index data/interim/pilot_index.json --out annotations/labels_auto.csv
python -m evaluate.run_eval --labels annotations/labels_auto.csv --out paper/manuscript/tables
python -m figures.plot_results --summary paper/manuscript/tables/eval_summary.json --out-dir paper/manuscript/figures
echo "Pilot pipeline complete."

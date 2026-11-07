#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
pytest -q
python -m aidev_extract.pilot --limit 200 --out data/interim/pilot_index.json
# Optional online fetch when index contains GitHub SHAs:
# python -m github_fetch.fetch_pairs --index data/interim/pilot_index.json --out data/processed/workflow_pairs
python -m labeling.prelabel --index data/interim/pilot_index.json --out annotations/labels_sample.csv
python -m evaluate.run_eval --labels annotations/labels_sample.csv --out paper/manuscript/tables
python -m figures.plot_results
python -m evaluate.ablation --labels annotations/labels_sample.csv --out paper/manuscript/tables/ablation.json
echo "Full local pipeline complete."

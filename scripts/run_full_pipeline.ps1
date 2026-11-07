$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
pytest -q
python -m aidev_extract.pilot --limit 200 --out data/interim/pilot_index.json
python -m labeling.prelabel --index data/interim/pilot_index.json --out annotations/labels_sample.csv
python -m evaluate.run_eval --labels annotations/labels_sample.csv --out paper/manuscript/tables
python -m figures.plot_results
python -m evaluate.ablation --labels annotations/labels_sample.csv --out paper/manuscript/tables/ablation.json
Write-Host "Full local pipeline complete."

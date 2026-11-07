# Publish this project to a public GitHub repository

This file is the complete handoff checklist. Follow it once; then send the URL and commit hash back so the manuscript can be stamped.

## Do NOT upload

- `.env` (tokens / secrets) — already listed in `.gitignore`
- `.venv/` and other local virtualenvs
- Large raw/interim AIDev dumps under `data/raw/`, `data/interim/`, `data/processed/` (gitignored; field labels + manifest are enough for reported metrics)
- Personal notes with credentials

## Do upload (core replication set)

- `src/`, `policies/`, `tests/`, `scripts/`
- `data/sample/` (controlled fixtures)
- `annotations/` (labels, field manifest, human round)
- `paper/manuscript/tables/` (frozen eval JSON/MD)
- `replication/` (this guide, REPRODUCE, DATA_CARD, ENV_FREEZE, SAMPLING_PROTOCOL)
- `requirements.txt`, `pyproject.toml`, `README.md`, `LICENSE`, `.gitignore`, `.env.example`

## Prerequisites on your PC

1. Install [Git for Windows](https://git-scm.com/download/win) and restart the terminal.
2. Create a GitHub account (if needed) and sign in at https://github.com
3. Optional but easier: install [GitHub CLI](https://cli.github.com/) (`gh`) and run `gh auth login`

## Step A — Create an empty public repository on GitHub

1. Open https://github.com/new
2. Repository name example: `github-actions-security-regression`
3. Visibility: **Public**
4. Do **not** add README / LICENSE / `.gitignore` on GitHub (this project already has them)
5. Click **Create repository**
6. Copy the URL shown, e.g. `https://github.com/YOUR_USER/github-actions-security-regression.git`

## Step B — First commit and push (PowerShell)

Open PowerShell in the project root (`مقاله روش پژوهش`):

```powershell
# 1) Confirm secrets will not be committed
git check-ignore -v .env
# Expected: .gitignore mentions .env

# 2) Initialize and commit
git init
git add .
git status
# Manually verify .env is NOT listed as staged

git commit -m "Initial public release: pin-semantics-v0.5 replication package"

# 3) Connect remote (paste YOUR url)
git branch -M main
git remote add origin https://github.com/YOUR_USER/github-actions-security-regression.git
git push -u origin main
```

If GitHub asks for login, use a Personal Access Token (classic) with `repo` scope, or sign in via GitHub CLI.

## Step C — Copy identifiers for the paper

1. Open the repository on GitHub.
2. Click the latest commit → copy the full **commit SHA** (40 hex chars).
3. Send both to the agent / paste into the manuscript:
   - Public URL: `https://github.com/YOUR_USER/github-actions-security-regression`
   - Commit: `________________________________________`

## After you send URL + commit

The manuscript placeholders `[URL_TO_BE_FILLED]` and `[COMMIT_TO_BE_FILLED]` will be replaced and Word files regenerated.

## Local smoke test after clone (for reviewers)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m pytest tests -q
python -m evaluate.run_eval --labels annotations/labels_sample.csv --out paper/manuscript/tables/controlled
```

See also `replication/REPRODUCE.md`.

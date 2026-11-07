"""Find workflow-touching PRs per AIDev agent via GitHub Pull Files API.

Faster than streaming millions of Codex-dominated commit-detail rows when seeking
Claude/Copilot/Cursor/Devin/Jules strata.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_RE = re.compile(r"\.github/workflows/[^/]+\.(yml|yaml)$", re.I)


def gh_headers() -> dict[str, str]:
    load_dotenv(ROOT / ".env")
    token = os.getenv("GITHUB_TOKEN", "").strip()
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "gha-security-regression-study",
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def repo_from_pr_row(row: pd.Series) -> str | None:
    for raw in (row.get("repo_url"), row.get("html_url")):
        if not isinstance(raw, str):
            continue
        m = re.search(r"github\.com/(?:repos/)?([^/]+/[^/]+)", raw)
        if m:
            return m.group(1).removesuffix(".git")
    return None


def list_pr_files(owner: str, repo: str, number: int) -> list[dict]:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files"
    files: list[dict] = []
    page = 1
    while page <= 5:
        r = requests.get(
            url,
            headers=gh_headers(),
            params={"per_page": 100, "page": page},
            timeout=60,
        )
        if r.status_code == 404:
            return []
        if r.status_code == 403:
            reset = r.headers.get("X-RateLimit-Reset")
            raise RuntimeError(f"GitHub 403 rate limit reset={reset}")
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        files.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return files


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--per-agent", type=int, default=25, help="Target workflow pairs per agent")
    p.add_argument("--max-prs-per-agent", type=int, default=120, help="PRs to probe per agent")
    p.add_argument(
        "--agents",
        type=str,
        default="Claude_Code,Copilot,Cursor,Devin,Google_Jules",
    )
    p.add_argument("--sleep", type=float, default=0.2)
    p.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data" / "interim" / "aidev_pass_b.json",
    )
    args = p.parse_args()

    load_dotenv(ROOT / ".env")
    if not os.getenv("GITHUB_TOKEN", "").strip():
        print("GITHUB_TOKEN missing")
        return 1

    pr_path = ROOT / "data" / "raw" / "aidev" / "pull_request.parquet"
    prs = pd.read_parquet(pr_path)
    wanted = [a.strip() for a in args.agents.split(",") if a.strip()]

    rows: list[dict] = []
    per_agent: dict[str, int] = {a: 0 for a in wanted}

    for agent in wanted:
        subset = prs[prs["agent"] == agent].sample(
            frac=1.0, random_state=42
        )  # shuffle
        print(f"=== {agent}: {len(subset)} PRs available, probing up to {args.max_prs_per_agent}")
        probed = 0
        for _, row in subset.iterrows():
            if per_agent[agent] >= args.per_agent:
                break
            if probed >= args.max_prs_per_agent:
                break
            probed += 1
            repo = repo_from_pr_row(row)
            if not repo or "/" not in repo:
                continue
            owner, name = repo.split("/", 1)
            number = int(row["number"])
            try:
                files = list_pr_files(owner, name, number)
                time.sleep(args.sleep)
            except Exception as exc:  # noqa: BLE001
                print(f"  skip {repo}#{number}: {exc}")
                time.sleep(max(args.sleep, 1.0))
                continue
            wf = [f for f in files if WORKFLOW_RE.search(str(f.get("filename", "")))]
            if not wf:
                continue
            # one row per workflow file (modified/added)
            for f in wf:
                status = f.get("status")
                if status not in ("modified", "added", "renamed", "changed"):
                    continue
                sha = None  # filled at fetch via PR API
                pair_id = f"aidev-{row['id']}-pr{number}-{Path(f['filename']).name}"
                rows.append(
                    {
                        "pair_id": pair_id,
                        "source": "aidev_github_sample",
                        "agent": agent,
                        "repo": repo,
                        "pr_id": int(row["id"]),
                        "pr_number": number,
                        "html_url": row.get("html_url"),
                        "filename": f["filename"],
                        "head_sha": None,
                        "base_sha": None,
                        "sha": None,
                        "status": status,
                        "message": str(row.get("title") or "")[:300],
                    }
                )
                per_agent[agent] += 1
                if per_agent[agent] >= args.per_agent:
                    break
            print(f"  hit {repo}#{number} -> +{len(wf)} workflow file(s); agent_total={per_agent[agent]}")

        print(f"done {agent}: kept={per_agent[agent]} probed={probed}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "count": len(rows),
        "per_agent": per_agent,
        "note": "SHAs resolved at fetch_pairs via Pulls API",
        "rows": rows,
    }
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Wrote {len(rows)} rows -> {args.out}")
    print("per_agent", per_agent)
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Stream AIDev pr_commit_details and keep only GitHub Actions workflow rows.

Avoids downloading the full ~12GB parquet. Joins local PR/repo tables for enrichment.
Supports agent-balanced collection and optional agent include/exclude filters.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_RE = re.compile(r"\.github/workflows/[^/]+\.(yml|yaml)$", re.I)


def is_workflow(path: object) -> bool:
    if not isinstance(path, str):
        return False
    return bool(WORKFLOW_RE.search(path.replace("\\", "/")))


def repo_from_url(repo_url: object, html_url: object) -> str | None:
    for raw in (repo_url, html_url):
        if not isinstance(raw, str) or not raw:
            continue
        m = re.search(r"github\.com/(?:repos/)?([^/]+/[^/]+)", raw)
        if m:
            return m.group(1).removesuffix(".git")
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=300, help="Max workflow rows to collect")
    parser.add_argument(
        "--per-agent-cap",
        type=int,
        default=80,
        help="Max rows kept per agent label (improves diversity)",
    )
    parser.add_argument(
        "--scan-max",
        type=int,
        default=2_000_000,
        help="Stop after scanning this many commit-detail rows",
    )
    parser.add_argument(
        "--exclude-agents",
        type=str,
        default="",
        help="Comma-separated agent names to skip (exact AIDev labels)",
    )
    parser.add_argument(
        "--include-agents",
        type=str,
        default="",
        help="If set, only keep these comma-separated agent labels",
    )
    parser.add_argument(
        "--allow-added",
        action="store_true",
        help="Also keep newly added workflow files",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data" / "interim" / "aidev_actions_index_enriched.json",
    )
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    token = os.getenv("HF_TOKEN", "").strip() or None
    if not token:
        print("HF_TOKEN missing in .env", file=sys.stderr)
        return 1

    import pandas as pd
    from datasets import load_dataset

    raw = ROOT / "data" / "raw" / "aidev"
    pr_path = raw / "pull_request.parquet"
    repo_path = raw / "repository.parquet"
    if not pr_path.exists() or not repo_path.exists():
        print("Need pull_request.parquet and repository.parquet under data/raw/aidev", file=sys.stderr)
        return 1

    exclude = {a.strip() for a in args.exclude_agents.split(",") if a.strip()}
    include = {a.strip() for a in args.include_agents.split(",") if a.strip()}

    print("Loading local PR/repo tables...")
    prs = pd.read_parquet(pr_path)
    repos = pd.read_parquet(repo_path)
    pr_by_id = prs.set_index("id", drop=False)
    repo_by_id = repos.set_index("id", drop=False)
    print(f"PRs={len(prs):,} repos={len(repos):,}")

    ok_status = {"modified", "changed", "renamed"}
    if args.allow_added:
        ok_status |= {"added"}

    print("Starting streaming scan of pr_commit_details (no full 12GB download)...")
    ds = load_dataset(
        "hao-li/AIDev",
        data_files="pr_commit_details.parquet",
        split="train",
        streaming=True,
        token=token,
    )

    rows: list[dict] = []
    seen: set[tuple] = set()
    per_agent: dict[str, int] = {}
    scanned = 0
    for rec in ds:
        scanned += 1
        if scanned % 50_000 == 0:
            print(f"  scanned={scanned:,} kept={len(rows)} agents={dict(per_agent)}")
        filename = rec.get("filename") or rec.get("file_name") or rec.get("path")
        if not is_workflow(filename):
            if scanned >= args.scan_max:
                break
            continue
        status = rec.get("status")
        if status not in ok_status and status is not None:
            if scanned >= args.scan_max:
                break
            continue

        pr_id = rec.get("pr_id")
        sha = rec.get("sha")
        dedupe_key = (pr_id, str(filename))
        if dedupe_key in seen:
            if scanned >= args.scan_max:
                break
            continue

        agent = ""
        repo = None
        pr_number = None
        html_url = None
        if pr_id is not None and pr_id in pr_by_id.index:
            pr = pr_by_id.loc[pr_id]
            if isinstance(pr, pd.DataFrame):
                pr = pr.iloc[0]
            agent = str(pr.get("agent") or "")
            pr_number = int(pr.get("number")) if pd.notna(pr.get("number")) else None
            html_url = pr.get("html_url")
            repo = repo_from_url(pr.get("repo_url"), html_url)
            rid = pr.get("repo_id")
            if (not repo) and rid is not None and rid in repo_by_id.index:
                r = repo_by_id.loc[rid]
                if isinstance(r, pd.DataFrame):
                    r = r.iloc[0]
                repo = str(r.get("full_name") or "") or None

        if exclude and agent in exclude:
            if scanned >= args.scan_max:
                break
            continue
        if include and agent not in include:
            if scanned >= args.scan_max:
                break
            continue
        if per_agent.get(agent, 0) >= args.per_agent_cap:
            if scanned >= args.scan_max:
                break
            continue

        pair_id = f"aidev-{pr_id}-{sha}-{Path(str(filename)).name}"
        rows.append(
            {
                "pair_id": pair_id,
                "source": "aidev_stream",
                "agent": agent,
                "repo": repo,
                "pr_id": pr_id,
                "pr_number": pr_number,
                "html_url": html_url,
                "filename": filename,
                "head_sha": sha,
                "sha": sha,
                "base_sha": None,
                "status": status,
                "additions": rec.get("additions"),
                "deletions": rec.get("deletions"),
                "message": (rec.get("message") or "")[:300],
            }
        )
        seen.add(dedupe_key)
        per_agent[agent] = per_agent.get(agent, 0) + 1
        if len(rows) >= args.limit or scanned >= args.scan_max:
            break

    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "count": len(rows),
        "scanned_commit_detail_rows": scanned,
        "per_agent": per_agent,
        "note": "base_sha is null; github_fetch will resolve via Pulls API",
        "rows": rows,
    }
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Wrote {len(rows)} workflow rows (scanned {scanned:,}) -> {args.out}")
    print("per_agent", per_agent)
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())

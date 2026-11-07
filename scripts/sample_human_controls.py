"""Sample human-authored workflow diffs from the same repos as agent field pairs.

Uses GitHub commits API filtered to .github/workflows path, excluding known bots.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BOT_HINTS = (
    "bot",
    "copilot",
    "codex",
    "cursor",
    "devin",
    "jules",
    "claude",
    "dependabot",
    "renovate",
    "github-actions",
)


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


def is_bot(login: str | None) -> bool:
    if not login:
        return True
    low = login.lower()
    return any(h in low for h in BOT_HINTS) or low.endswith("[bot]")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--from-index",
        type=Path,
        default=ROOT / "data" / "interim" / "aidev_pass_a.json",
        help="Agent index used to harvest repo list",
    )
    p.add_argument("--limit", type=int, default=80)
    p.add_argument("--per-repo", type=int, default=3)
    p.add_argument("--sleep", type=float, default=0.25)
    p.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data" / "interim" / "human_controls_index.json",
    )
    args = p.parse_args()

    load_dotenv(ROOT / ".env")
    data = json.loads(args.from_index.read_text(encoding="utf-8"))
    agent_rows = data.get("rows", data if isinstance(data, list) else [])
    repos = sorted({r.get("repo") for r in agent_rows if r.get("repo")})
    print(f"Repos to probe: {len(repos)}")

    rows: list[dict] = []
    seen_files: set[tuple[str, str]] = set()

    for repo in repos:
        if len(rows) >= args.limit:
            break
        if not repo or "/" not in repo:
            continue
        owner, name = repo.split("/", 1)
        url = f"https://api.github.com/repos/{owner}/{name}/commits"
        try:
            r = requests.get(
                url,
                headers=gh_headers(),
                params={"path": ".github/workflows", "per_page": 30},
                timeout=60,
            )
            time.sleep(args.sleep)
            if r.status_code in (404, 409):
                continue
            if r.status_code == 403:
                raise RuntimeError(f"403 rate limit reset={r.headers.get('X-RateLimit-Reset')}")
            r.raise_for_status()
            commits = r.json()
        except Exception as exc:  # noqa: BLE001
            print(f"skip {repo}: {exc}")
            continue

        got = 0
        for c in commits:
            if len(rows) >= args.limit or got >= args.per_repo:
                break
            author = (c.get("author") or {}).get("login") or (c.get("commit") or {}).get("author", {}).get("name")
            if is_bot(str(author) if author else None):
                continue
            sha = c.get("sha")
            parents = c.get("parents") or []
            if not sha or not parents:
                continue
            base = parents[0].get("sha")
            # list files in commit
            cr = requests.get(
                f"https://api.github.com/repos/{owner}/{name}/commits/{sha}",
                headers=gh_headers(),
                timeout=60,
            )
            time.sleep(args.sleep)
            if cr.status_code != 200:
                continue
            files = cr.json().get("files") or []
            for f in files:
                fn = f.get("filename") or ""
                if not re.search(r"\.github/workflows/[^/]+\.(yml|yaml)$", fn, re.I):
                    continue
                if f.get("status") not in ("modified", "added", "renamed", "changed"):
                    continue
                key = (repo, fn, sha)
                if key in seen_files:
                    continue
                seen_files.add(key)
                pair_id = f"human-{owner}_{name}-{sha[:12]}-{Path(fn).name}"
                rows.append(
                    {
                        "pair_id": pair_id,
                        "source": "human_repo_control",
                        "agent": "human",
                        "repo": repo,
                        "pr_id": None,
                        "pr_number": None,
                        "html_url": c.get("html_url"),
                        "filename": fn,
                        "head_sha": sha,
                        "base_sha": base,
                        "sha": sha,
                        "status": f.get("status"),
                        "message": ((c.get("commit") or {}).get("message") or "")[:300],
                    }
                )
                got += 1
                if got >= args.per_repo or len(rows) >= args.limit:
                    break
        if got:
            print(f"  {repo}: +{got} human workflow commits")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"count": len(rows), "rows": rows}
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Wrote {len(rows)} human control rows -> {args.out}")
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())

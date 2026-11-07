from __future__ import annotations

import argparse
import base64
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


def gh_headers() -> dict[str, str]:
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN", "").strip()
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "gha-security-regression-study",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def get_file_at_ref(owner: str, repo: str, path: str, ref: str) -> str | None:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    r = requests.get(url, headers=gh_headers(), params={"ref": ref}, timeout=60)
    if r.status_code == 404:
        return None
    if r.status_code == 403:
        # rate limit
        reset = r.headers.get("X-RateLimit-Reset")
        raise RuntimeError(f"GitHub API 403 (rate limit?). reset={reset}")
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    return None


def resolve_pr_shas(owner: str, repo: str, pr_number: int) -> tuple[str | None, str | None]:
    """Return (base_sha, head_sha) for a pull request."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    r = requests.get(url, headers=gh_headers(), timeout=60)
    if r.status_code == 404:
        return None, None
    if r.status_code == 403:
        reset = r.headers.get("X-RateLimit-Reset")
        raise RuntimeError(f"GitHub API 403 (rate limit?). reset={reset}")
    r.raise_for_status()
    data = r.json()
    base = (data.get("base") or {}).get("sha")
    head = (data.get("head") or {}).get("sha")
    return base, head


def parent_sha(owner: str, repo: str, sha: str) -> str | None:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/commits/{sha}"
    r = requests.get(url, headers=gh_headers(), timeout=60)
    if r.status_code == 404:
        return None
    if r.status_code == 403:
        reset = r.headers.get("X-RateLimit-Reset")
        raise RuntimeError(f"GitHub API 403 (rate limit?). reset={reset}")
    r.raise_for_status()
    parents = r.json().get("parents") or []
    if not parents:
        return None
    return parents[0].get("sha")


def save_pair(
    out_dir: Path,
    pair_id: str,
    before_text: str,
    after_text: str,
    filename: str = "ci.yml",
) -> dict[str, str]:
    base = out_dir / pair_id
    (base / "before").mkdir(parents=True, exist_ok=True)
    (base / "after").mkdir(parents=True, exist_ok=True)
    name = Path(filename).name
    before_path = base / "before" / name
    after_path = base / "after" / name
    before_path.write_text(before_text, encoding="utf-8")
    after_path.write_text(after_text, encoding="utf-8")
    return {"before_path": str(before_path), "after_path": str(after_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch before/after workflow pairs from GitHub")
    parser.add_argument("--index", type=Path, required=True, help="JSON index with PR metadata")
    parser.add_argument("--out", type=Path, default=Path("data/processed/workflow_pairs"))
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args(argv)

    index = json.loads(args.index.read_text(encoding="utf-8"))
    rows = index.get("rows", index if isinstance(index, list) else [])
    results = []
    for row in rows:
        # Synthetic rows already have paths
        if row.get("before_path") and row.get("after_path"):
            results.append(row)
            continue
        owner_repo = row.get("repo") or row.get("repo_full_name")
        if not owner_repo or "/" not in str(owner_repo):
            continue
        owner, repo = str(owner_repo).split("/", 1)
        path = row.get("filename") or row.get("path")
        base_sha = row.get("base_sha") or row.get("before_sha")
        head_sha = row.get("head_sha") or row.get("after_sha") or row.get("sha")
        try:
            if (not base_sha or not head_sha) and row.get("pr_number"):
                b, h = resolve_pr_shas(owner, repo, int(row["pr_number"]))
                time.sleep(args.sleep)
                base_sha = base_sha or b
                head_sha = head_sha or h
            if not base_sha and head_sha:
                base_sha = parent_sha(owner, repo, str(head_sha))
                time.sleep(args.sleep)
            if not (path and head_sha):
                continue
            after = get_file_at_ref(owner, repo, path, str(head_sha))
            time.sleep(args.sleep)
            if row.get("status") == "added" or base_sha is None:
                before = ""  # new file: empty before
            else:
                before = get_file_at_ref(owner, repo, path, str(base_sha))
                time.sleep(args.sleep)
                if before is None:
                    before = ""
        except Exception as exc:  # noqa: BLE001
            print(f"fetch failed for {owner_repo} {path}: {exc}")
            continue
        if after is None:
            continue
        pair_id = str(row.get("pair_id") or f"{owner}_{repo}_{row.get('pr_number', 'na')}")
        paths = save_pair(args.out, pair_id, before or "", after, filename=path)
        results.append({**row, "base_sha": base_sha, "head_sha": head_sha, **paths})

    out_index = args.out / "pairs_index.json"
    args.out.mkdir(parents=True, exist_ok=True)
    out_index.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Saved {len(results)} pairs -> {out_index}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

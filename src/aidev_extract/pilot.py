from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

WORKFLOW_RE = re.compile(r"\.github/workflows/[^/]+\.(yml|yaml)$", re.I)


def is_workflow_path(path: str) -> bool:
    if not isinstance(path, str):
        return False
    return bool(WORKFLOW_RE.search(path.replace("\\", "/")))


def filter_workflow_rows(df: pd.DataFrame, filename_col: str = "filename") -> pd.DataFrame:
    if filename_col not in df.columns:
        # try common alternatives
        for alt in ("file_name", "path", "filename_new", "previous_filename"):
            if alt in df.columns:
                filename_col = alt
                break
        else:
            raise KeyError(f"No filename column in {list(df.columns)}")
    mask = df[filename_col].astype(str).map(is_workflow_path)
    return df.loc[mask].copy()


def try_load_commit_details(limit_rows: int | None = None) -> pd.DataFrame | None:
    """Load AIDev pr_commit_details with memory-safe patterns when available."""
    load_dotenv()
    revision = os.getenv("AIDEV_REVISION", "v4")
    # Prefer HF hub parquet URIs; fall back to local cache paths
    uris = [
        f"hf://datasets/hao-li/AIDev@{revision}/pr_commit_details.parquet",
        f"hf://datasets/hao-li/AIDev/pr_commit_details.parquet",
        "data/raw/pr_commit_details.parquet",
    ]
    for uri in uris:
        try:
            if uri.startswith("hf://"):
                df = pd.read_parquet(uri)
            else:
                p = Path(uri)
                if not p.exists():
                    continue
                df = pd.read_parquet(p)
            if limit_rows:
                df = df.head(limit_rows)
            return df
        except Exception as exc:  # noqa: BLE001
            print(f"[skip] {uri}: {exc}")
            continue
    return None


def build_synthetic_pilot(limit: int = 50) -> list[dict]:
    """Offline pilot index from bundled samples for reproducibility without HF."""
    root = Path("data/sample")
    rows = []
    agents = ["copilot", "codex", "cursor", "devin", "claude_code", "jules"]
    for i, sample_dir in enumerate(sorted(root.iterdir())):
        if not sample_dir.is_dir():
            continue
        before = sample_dir / "before" / "ci.yml"
        after = sample_dir / "after" / "ci.yml"
        if not before.exists() or not after.exists():
            continue
        name = sample_dir.name
        if name.startswith("human_") or name.startswith("safe_") or name.startswith(
            "no_regression"
        ):
            agent = "human"
        else:
            agent = agents[i % len(agents)]
        is_regression = not (
            name.startswith("safe_")
            or name.startswith("no_regression")
            or name == "human_safe_pin"
        )
        rows.append(
            {
                "pair_id": f"sample-{name}",
                "source": "synthetic_sample",
                "agent": agent,
                "repo": "local/sample",
                "pr_number": i + 1,
                "filename": ".github/workflows/ci.yml",
                "before_path": str(before.as_posix()),
                "after_path": str(after.as_posix()),
                "expected_regression": is_regression,
            }
        )
        if len(rows) >= limit:
            break
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pilot extraction of Actions changes from AIDev")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--out", type=Path, default=Path("data/interim/pilot_index.json"))
    parser.add_argument(
        "--synthetic-only",
        action="store_true",
        help="Skip Hugging Face and only use bundled samples",
    )
    parser.add_argument(
        "--scan-rows",
        type=int,
        default=200_000,
        help="Max rows to scan from pr_commit_details when online",
    )
    args = parser.parse_args(argv)

    rows: list[dict] = []
    if not args.synthetic_only:
        df = try_load_commit_details(limit_rows=args.scan_rows)
        if df is not None:
            print(f"Loaded commit details shape={df.shape} cols={list(df.columns)[:20]}")
            try:
                wf = filter_workflow_rows(df)
                print(f"Workflow file changes found in scan: {len(wf)}")
                # Keep a compact index; full before/after fetch is a separate step
                keep_cols = [c for c in df.columns if c in wf.columns]
                sample = wf.head(args.limit)
                for _, r in sample.iterrows():
                    rows.append({k: (None if pd.isna(r[k]) else r[k]) for k in keep_cols})
            except Exception as exc:  # noqa: BLE001
                print(f"Filter failed, falling back to synthetic: {exc}")

    if not rows:
        print("Using synthetic bundled samples for pilot index")
        rows = build_synthetic_pilot(limit=args.limit)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(
            {
                "count": len(rows),
                "rows": rows,
                "note": "Pilot index; fetch_workflow_pairs fills YAML content when using AIDev",
            },
            f,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    print(f"Wrote {len(rows)} rows -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Attempt a bounded AIDev download / listing for field-study readiness."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "aidev_field_status.json"
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

status: dict = {"ok": False, "steps": []}


def step(name: str, **kwargs):
    status["steps"].append({"name": name, **kwargs})
    print(name, kwargs)


def main() -> int:
    load_dotenv(ROOT / ".env")
    token = os.getenv("HF_TOKEN", "").strip() or None
    step("auth", hf_token_set=bool(token))

    try:
        from huggingface_hub import hf_hub_download, list_repo_files
    except Exception as e:  # noqa: BLE001
        step("import_huggingface_hub", error=str(e))
        OUT.write_text(json.dumps(status, indent=2), encoding="utf-8")
        return 1

    try:
        files = list_repo_files("hao-li/AIDev", repo_type="dataset", token=token)
        interesting = [f for f in files if any(k in f.lower() for k in ("commit", "pull", "parquet"))]
        step("list_repo_files", n_files=len(files), interesting=interesting[:40])
    except Exception as e:  # noqa: BLE001
        step("list_repo_files", error=str(e))
        OUT.write_text(json.dumps(status, indent=2), encoding="utf-8")
        return 1

    # Prefer smaller metadata tables. Skip full pr_commit_details (~12GB);
    # use scripts/stream_aidev_workflows.py for workflow extraction instead.
    candidates = [
        "pull_request.parquet",
        "pr_commits.parquet",
        "repository.parquet",
    ]
    downloaded = []
    for name in candidates:
        if name not in files and not any(f.endswith(name) for f in files):
            # try nested paths
            matches = [f for f in files if f.endswith(name)]
            if not matches:
                step("skip_missing", file=name)
                continue
            name = matches[0]
        try:
            path = hf_hub_download(
                repo_id="hao-li/AIDev",
                repo_type="dataset",
                filename=name if "/" in name else name,
                local_dir=str(RAW / "aidev"),
                token=token,
            )
            downloaded.append(path)
            step("downloaded", file=name, path=path)
            # Stop after first successful commit-details-like download attempt budget:
            if "commit_details" in name.replace("\\", "/").lower():
                break
            if len(downloaded) >= 2 and "pull_request" in "".join(downloaded).lower():
                # enough to prove connectivity; details may be huge
                if not any("commit_details" in d.lower() for d in downloaded):
                    # try commit details once more if listed
                    continue
                break
        except Exception as e:  # noqa: BLE001
            step("download_fail", file=name, error=str(e))

    # If we got pr_commit_details locally, run a tiny workflow filter
    details = None
    for p in downloaded:
        if "commit_details" in p.lower():
            details = p
            break
    if details:
        try:
            import pandas as pd
            from aidev_extract.pilot import filter_workflow_rows

            df = pd.read_parquet(details)
            step("loaded_details", shape=list(df.shape), columns=list(df.columns)[:25])
            # try common filename columns
            for col in ("filename", "file_name", "path", "previous_filename"):
                if col in df.columns:
                    wf = filter_workflow_rows(df, filename_col=col)
                    sample = wf.head(20)
                    out_idx = ROOT / "data" / "interim" / "aidev_actions_index.json"
                    rows = sample.to_dict(orient="records")
                    out_idx.write_text(
                        json.dumps({"count": len(rows), "rows": rows}, indent=2, default=str),
                        encoding="utf-8",
                    )
                    step("filtered_workflows", n=int(len(wf)), sample_written=str(out_idx))
                    status["ok"] = True
                    break
        except Exception as e:  # noqa: BLE001
            step("filter_fail", error=str(e))
    else:
        step(
            "no_commit_details_yet",
            note="Connectivity/listing may work; full commit_details download still required for field eval",
        )
        # Mark partial success if any file downloaded
        status["ok"] = bool(downloaded)

    OUT.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print("Wrote", OUT)
    return 0 if status.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import csv
import hashlib
import json
import platform
import shutil
import sys
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "annotations" / "labels_aidev.csv"
out = root / "annotations" / "field_pairs_manifest_330.csv"
rows = list(csv.DictReader(src.open(encoding="utf-8")))
assert len(rows) == 330, len(rows)
fields = [
    "pair_id",
    "agent",
    "source",
    "before_path",
    "after_path",
    "gold_has_regression",
    "gold_rule_ids",
    "annotator",
    "notes",
]
with out.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in fields})

h = hashlib.sha256(out.read_bytes()).hexdigest()
meta = {
    "n": 330,
    "path": str(out.relative_to(root)).replace("\\", "/"),
    "sha256": h,
    "strata": dict(sorted(Counter(r["agent"] for r in rows).items())),
    "gold_positives": sum(
        1 for r in rows if r.get("gold_has_regression") in ("1", "true", "True")
    ),
}
(root / "annotations" / "field_pairs_manifest_330.meta.json").write_text(
    json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)
print("wrote", out.name, "n=", len(rows), "gold+", meta["gold_positives"])

try:
    import pytest
    import ruamel.yaml

    yaml_v = getattr(ruamel.yaml, "__version__", "?")
    pytest_v = getattr(pytest, "__version__", "?")
except Exception as e:  # pragma: no cover
    yaml_v = pytest_v = str(e)

env = {
    "os": platform.platform(),
    "python": sys.version.split()[0],
    "machine": platform.machine(),
    "processor": platform.processor(),
    "cpu_count_logical": __import__("os").cpu_count(),
    "packages": {"ruamel.yaml": yaml_v, "pytest": pytest_v},
    "zizmor_on_path": bool(shutil.which("zizmor")),
}
(root / "replication" / "ENV_FREEZE.json").write_text(
    json.dumps(env, indent=2) + "\n", encoding="utf-8"
)
print("env freeze written")

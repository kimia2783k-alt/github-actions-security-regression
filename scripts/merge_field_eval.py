"""Merge Codex + multi-agent + human field pairs, gold-audit, and evaluate."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_pairs(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return data.get("rows", [])


def main() -> int:
    parts = [
        ROOT / "data" / "processed" / "workflow_pairs" / "pairs_index.json",  # Codex
        ROOT / "data" / "processed" / "workflow_pairs_b" / "pairs_index.json",
        ROOT / "data" / "processed" / "workflow_pairs_human" / "pairs_index.json",
    ]
    rows: list[dict] = []
    seen: set[str] = set()
    for p in parts:
        for r in load_pairs(p):
            if not r.get("before_path") or not r.get("after_path"):
                continue
            pid = str(r.get("pair_id"))
            if pid in seen:
                continue
            seen.add(pid)
            rows.append(r)

    merged_index = ROOT / "data" / "processed" / "workflow_pairs_merged" / "pairs_index.json"
    merged_index.parent.mkdir(parents=True, exist_ok=True)
    merged_index.write_text(json.dumps(rows, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"merged pairs={len(rows)} -> {merged_index}")

    labels = ROOT / "annotations" / "labels_aidev_merged.csv"
    subprocess.check_call(
        [sys.executable, "-m", "labeling.prelabel", "--index", str(merged_index), "--out", str(labels)],
        cwd=str(ROOT),
    )
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "field_gold_audit.py")], cwd=str(ROOT))
    # field_gold_audit writes gold_overrides from labels_aidev.csv by default — point it at merged
    # Re-run audit inline against merged labels:
    subprocess.check_call(
        [
            sys.executable,
            "-c",
            f"""
from pathlib import Path
import csv, json, re
USES_RE=re.compile(r'(?m)^\\s*-?\\s*uses:\\s*([^\\s#]+)')
SHA=re.compile(r'^[0-9a-f]{{40}}$')
TRUSTED=('actions/','github/','aquasecurity/','./')
def actions(path):
    text=Path(path).read_text(encoding='utf-8',errors='replace')
    return {{m.group(1).strip() for m in USES_RE.finditer(text) if m.group(1) and ('/' in m.group(1) or m.group(1).startswith('./'))}}
def parse(u):
    return (u.rsplit('@',1)+[''])[:2] if '@' in u else (u,'')
labels=Path(r'{labels.as_posix()}')
rows=list(csv.DictReader(labels.open(encoding='utf-8')))
for r in rows:
    b_acts,a_acts=actions(Path(r['before_path'])),actions(Path(r['after_path']))
    new=a_acts-b_acts
    b_map={{parse(u)[0]:parse(u)[1] for u in b_acts}}
    a_map={{parse(u)[0]:parse(u)[1] for u in a_acts}}
    unpin=[]
    for name,bref in b_map.items():
        aref=a_map.get(name)
        if aref is None: continue
        if SHA.fullmatch(bref) and not SHA.fullmatch(aref):
            unpin.append(name)
    gold=0; rules=[]; notes=[]
    if unpin:
        gold=1; rules.append('R05'); notes.append('unpin')
    for u in new:
        name,ref=parse(u)
        if name.startswith(TRUSTED) or name.startswith('./'):
            continue
        if not SHA.fullmatch(ref):
            gold=1; rules.append('R06'); notes.append('new:'+u)
    bt=Path(r['before_path']).read_text(encoding='utf-8',errors='replace')
    at=Path(r['after_path']).read_text(encoding='utf-8',errors='replace')
    if re.search(r'permissions:\\s*write-all', at) and not re.search(r'permissions:\\s*write-all', bt):
        gold=1; rules.append('R01')
    if 'pull_request_target' in at and 'pull_request_target' not in bt:
        gold=1; rules.append('R03')
    if re.search(r'self-hosted', at) and not re.search(r'self-hosted', bt):
        gold=1; rules.append('R11')
    r['gold_has_regression']=str(int(gold))
    r['gold_rule_ids']='|'.join(sorted(set(rules)))
    r['annotator']='field_audit_v2'
    r['notes']=';'.join(notes) or ('neg' if gold==0 else 'pos')
with labels.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
pos=sum(1 for r in rows if r['gold_has_regression']=='1')
from collections import Counter
print('n',len(rows),'gold_pos',pos)
print('by_agent_rate', {{a: round(sum(1 for r in rows if r['agent']==a and r['gold_has_regression']=='1')/max(1,sum(1 for r in rows if r['agent']==a)),3) for a in sorted(set(r['agent'] for r in rows))}})
print('counts', dict(Counter(r['agent'] for r in rows)))
""",
        ],
        cwd=str(ROOT),
    )

    out = ROOT / "paper" / "manuscript" / "tables" / "field"
    subprocess.check_call(
        [sys.executable, "-m", "evaluate.run_eval", "--labels", str(labels), "--out", str(out)],
        cwd=str(ROOT),
    )
    # also refresh primary labels_aidev.csv as the merged set
    labels.replace(ROOT / "annotations" / "labels_aidev.csv") if False else None
    (ROOT / "annotations" / "labels_aidev.csv").write_text(labels.read_text(encoding="utf-8"), encoding="utf-8")
    print("updated annotations/labels_aidev.csv and field tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

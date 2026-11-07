from pathlib import Path

from policy_validator.validator import validate_paths

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample"


def _pair(name: str):
    return SAMPLE / name / "before" / "ci.yml", SAMPLE / name / "after" / "ci.yml"


def test_r01_permissions_write_all():
    before, after = _pair("r01_permissions_write_all")
    findings = validate_paths(before, after)
    ids = {f.rule_id for f in findings}
    assert "R01" in ids


def test_r03_pr_target():
    before, after = _pair("r03_pr_target")
    findings = validate_paths(before, after)
    ids = {f.rule_id for f in findings}
    assert "R03" in ids
    assert "R04" in ids


def test_r05_unpinned():
    before, after = _pair("r05_unpinned_action")
    findings = validate_paths(before, after)
    ids = {f.rule_id for f in findings}
    assert "R05" in ids


def test_r08_removed_security_job():
    before, after = _pair("r08_removed_security_job")
    findings = validate_paths(before, after)
    ids = {f.rule_id for f in findings}
    assert "R08" in ids


def test_safe_change_no_regression():
    before, after = _pair("safe_change")
    findings = validate_paths(before, after)
    ids = {f.rule_id for f in findings if f.rule_id != "PARSE"}
    assert ids == set()

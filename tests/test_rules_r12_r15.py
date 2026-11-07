from pathlib import Path

from policy_validator.validator import validate_paths

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample"


def _pair(name: str):
    return SAMPLE / name / "before" / "ci.yml", SAMPLE / name / "after" / "ci.yml"


def test_r12_dangerous_scopes():
    ids = {f.rule_id for f in validate_paths(*_pair("r12_contents_write"))}
    assert "R12" in ids


def test_r13_curl_bash():
    ids = {f.rule_id for f in validate_paths(*_pair("r13_curl_bash"))}
    assert "R13" in ids


def test_r14_issue_comment():
    ids = {f.rule_id for f in validate_paths(*_pair("r14_issue_comment"))}
    assert "R14" in ids


def test_r15_github_env():
    ids = {f.rule_id for f in validate_paths(*_pair("r15_github_env"))}
    assert "R15" in ids


def test_r01_write_all_does_not_require_r12():
    """Blanket write-all is R01; R12 deferred for that case."""
    ids = {f.rule_id for f in validate_paths(*_pair("r01_permissions_write_all"))}
    assert "R01" in ids
    assert "R12" not in ids

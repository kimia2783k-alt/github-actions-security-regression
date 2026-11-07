from pathlib import Path

from policy_validator.validator import validate_paths
from workflow_parse.signals import extract_signals_from_path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample"


def _pair(name: str):
    return SAMPLE / name / "before" / "ci.yml", SAMPLE / name / "after" / "ci.yml"


def test_r05_comment_only_sha_not_a_pin_and_not_r05():
    """uses: owner/action@v4 # <sha> is NOT effectively pinned."""
    before, after = _pair("r05_comment_pin_lost")
    b = extract_signals_from_path(before)
    assert any(a.comment_sha and not a.effectively_pinned for a in b.actions)
    ids = {f.rule_id for f in validate_paths(before, after)}
    assert "R05" not in ids


def test_r05_real_sha_unpin_still_fires():
    before, after = _pair("r05_unpinned_action")
    ids = {f.rule_id for f in validate_paths(before, after)}
    assert "R05" in ids


def test_r09_workflow_run():
    before, after = _pair("r09_workflow_run")
    ids = {f.rule_id for f in validate_paths(before, after)}
    assert "R09" in ids


def test_r06_identity_not_r05_for_brand_new():
    before, after = _pair("r06_new_unpinned_third_party")
    ids = {f.rule_id for f in validate_paths(before, after)}
    assert "R06" in ids
    assert "R05" not in ids


def test_r07_r10_r11():
    assert "R07" in {f.rule_id for f in validate_paths(*_pair("r07_secret_echo"))}
    assert "R10" in {f.rule_id for f in validate_paths(*_pair("r10_script_injection"))}
    assert "R11" in {f.rule_id for f in validate_paths(*_pair("r11_self_hosted"))}

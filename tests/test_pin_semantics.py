"""Pin semantics: only @ref 40-hex SHA counts as effectively_pinned."""
from __future__ import annotations

from pathlib import Path

from policy_validator.validator import validate_paths
from workflow_parse.signals import extract_signals_from_path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample"


def _pair(name: str):
    return SAMPLE / name / "before" / "ci.yml", SAMPLE / name / "after" / "ci.yml"


def test_real_commit_ref_is_effectively_pinned():
    before, _ = _pair("r05_unpinned_action")
    sig = extract_signals_from_path(before)
    checkout = next(a for a in sig.actions if a.name == "checkout")
    assert checkout.pinned_sha is True
    assert checkout.effectively_pinned is True
    assert len(checkout.ref) == 40


def test_floating_tag_not_effectively_pinned():
    _, after = _pair("r05_unpinned_action")
    sig = extract_signals_from_path(after)
    checkout = next(a for a in sig.actions if a.name == "checkout")
    assert checkout.ref == "v4"
    assert checkout.pinned_sha is False
    assert checkout.effectively_pinned is False


def test_comment_only_sha_is_not_effective_pin():
    before, after = _pair("r05_comment_pin_lost")
    b = extract_signals_from_path(before)
    checkout_b = next(a for a in b.actions if a.name == "checkout")
    assert checkout_b.ref == "v4"
    assert checkout_b.comment_sha  # comment may still be recorded
    assert checkout_b.effectively_pinned is False

    a = extract_signals_from_path(after)
    checkout_a = next(x for x in a.actions if x.name == "checkout")
    assert checkout_a.ref == "v4"
    assert checkout_a.effectively_pinned is False

    # Losing a documentation comment is not an R05 regression.
    ids = {f.rule_id for f in validate_paths(before, after)}
    assert "R05" not in ids


def test_sha_pin_lost_to_floating_tag_is_r05():
    before, after = _pair("r05_unpinned_action")
    ids = {f.rule_id for f in validate_paths(before, after)}
    assert "R05" in ids

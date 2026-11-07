from pathlib import Path

from policy_validator.validator import validate_paths

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample"


def _pair(name: str):
    return SAMPLE / name / "before" / "ci.yml", SAMPLE / name / "after" / "ci.yml"


def test_r02_and_r06_and_negatives():
    f02 = {f.rule_id for f in validate_paths(*_pair("r02_permissions_removed"))}
    assert "R02" in f02

    f06 = {f.rule_id for f in validate_paths(*_pair("r06_new_unpinned_third_party"))}
    assert "R06" in f06

    f_safe = {f.rule_id for f in validate_paths(*_pair("safe_add_codeql")) if f.rule_id != "PARSE"}
    assert f_safe == set()

    f_keep = {
        f.rule_id
        for f in validate_paths(*_pair("no_regression_already_write_all"))
        if f.rule_id != "PARSE"
    }
    assert f_keep == set()

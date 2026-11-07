from baselines.zizmor_baseline import _finding_key, _finding_keys


def test_finding_key_prefers_ident():
    f = {"ident": "abc", "message": "x"}
    assert _finding_key(f) == "abc"


def test_finding_keys_detect_new():
    before = [{"ident": "a"}, {"ident": "b"}]
    after = [{"ident": "a"}, {"ident": "b"}, {"ident": "c"}]
    assert _finding_keys(after) - _finding_keys(before) == {"c"}


def test_finding_key_fallback_stable():
    f1 = {"kind": "template-injection", "location": {"line": 3}}
    f2 = {"kind": "template-injection", "location": {"line": 3}}
    assert _finding_key(f1) == _finding_key(f2)

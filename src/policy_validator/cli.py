from __future__ import annotations

import argparse
import sys
from pathlib import Path

from policy_validator.validator import findings_to_json, validate_paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect security regressions between two GitHub Actions workflow files"
    )
    parser.add_argument("before", type=Path, help="Path to before YAML")
    parser.add_argument("after", type=Path, help="Path to after YAML")
    parser.add_argument(
        "--rules",
        type=Path,
        default=None,
        help="Path to rules YAML (default: policies/owasp_cicd_rules.yaml)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)

    findings = validate_paths(args.before, args.after, args.rules)
    if args.json:
        print(findings_to_json(findings))
    else:
        if not findings:
            print("PASS: no security regressions detected")
            return 0
        print(f"FAIL: {len(findings)} finding(s)")
        for f in findings:
            print(f"  [{f.severity}] {f.rule_id}: {f.message}")
            print(f"           evidence: {f.evidence}")
            if f.owasp:
                print(f"           owasp: {', '.join(f.owasp)}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())

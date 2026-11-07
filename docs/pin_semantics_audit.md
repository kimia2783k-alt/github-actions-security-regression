# Pin semantics audit (R05 / R06)

## Finding

Prior logic could treat a 40-hex token in a YAML line comment as contributing to “effective” pinning while `uses: owner/action@v4` still referenced a floating tag.

## Policy (frozen)

In `src/workflow_parse/signals.py`, `ActionRef.effectively_pinned` equals `pinned_sha` where `pinned_sha` is true **only** when the `@ref` itself is a 40-character hexadecimal commit SHA.

Comment SHA (`# <sha>`) may still be parsed into `comment_sha` for diagnostics but **must not** satisfy R05/R06 pin predicates.

## Tests

`tests/test_pin_semantics.py` covers:

- Positive: real `@<40hex>` commit pin
- Negative: floating `@v4` / `@main`
- Negative: floating tag with comment-only `# <40hex>` (not a pin)

Non-example fixture: `data/sample/r05_comment_pin_lost`.

## Re-evaluation

After the fix, controlled + field + human gold evals were re-run. Manuscript tables must match:

- `paper/manuscript/tables/field/eval_summary.json`
- `paper/manuscript/tables/field/eval_human_gold.json`
- `paper/manuscript/tables/field/confusion_matrices.md`

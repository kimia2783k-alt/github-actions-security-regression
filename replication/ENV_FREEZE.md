# Hardware / software freeze (evaluation host)

Freeze id: **pin-semantics-v0.5**  
Machine-readable companion: `ENV_FREEZE.json`.

## Software

| Component | Version (this freeze) |
|-----------|------------------------|
| OS | Windows 11 (build 10.0.26200) |
| Python | 3.14.7 |
| YAML parser | `ruamel.yaml` 0.19.1 |
| Statistics | `scipy` 1.18.1 (`chi2_contingency`, default Yates correction for 2×2) |
| Tests | `pytest` 9.1.1 |
| zizmor CLI | 1.31.1 (`zizmor_cli_available: true` in field eval JSON) |

## Hardware

| Item | Value |
|------|-------|
| Machine | AMD64 |
| CPU | Intel64 Family 6 Model 183 Stepping 1 (24 logical) |
| GPU | Not required |

## Pin semantics (R05/R06)

Effective Action pin = `uses` `@ref` matching `^[0-9a-f]{40}$` only.  
A trailing `# <40hex>` comment next to a floating tag is **not** an effective pin.

## Still author-filled before submission

- Public repository URL
- Release tag / commit hash of the published replication package

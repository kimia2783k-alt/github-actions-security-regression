# Gold-label version delta (same N=330 set)

Reconstruction note: interim/v2 columns are **reconstructed** by replaying
historical audit predicates on the same paths; v3 is the current CSV gold.

| Version | Predicate family | Gold positives | Rate |
|---|---|---:|---:|
| Interim (reconstructed) | R01/R03/R05/R06*/R09/R11; docker not trusted | 40 | 0.121 |
| v2 (reconstructed) | + trusted docker/formal pin; still no R12–R15 | 33 | 0.100 |
| **v3 (current)** | + R12–R15 + formal signals | **46** | **0.139** |

\*Interim R06 treated `docker/*` as third-party.


Newly positive vs interim: **12**; flipped interim→neg under v3: **6**.

## Rule tags among newly-positive pairs (count of rule appearances)

| Rule | Count |
|---|---:|
| R12 | 8 |
| R15 | 3 |
| R13 | 1 |

## Sample newly-positive pair_ids (up to 15)

| pair_id | agent | gold_rule_ids |
|---|---|---|
| `aidev-4021402504-07ea82edb4428f334fca588d131875957bceadb2-release.yml` | OpenAI_Codex | R12 |
| `aidev-4074830790-5645ffcaaecfa5df91c0d022ae7c756cf5e5ea74-openclaw-npm-r` | OpenAI_Codex | R12 |
| `aidev-4116091058-6ae1582aec17a39b9d30fe1d589ff422c214c70a-ci.yml` | OpenAI_Codex | R15 |
| `aidev-3530137270-e972b210c577f46199eddd2e5c50c5b984768f64-release.yml` | OpenAI_Codex | R12 |
| `aidev-3985709913-a7d0b1211085810fc5c013c50358de62535a0ab7-create-release` | OpenAI_Codex | R12 |
| `aidev-4123369821-b76853e69b57e64772818cd5240c0e367a2f7891-publish-ts.yml` | OpenAI_Codex | R12 |
| `aidev-4118855135-0af2bcf7eed139433f1f1983ef275b3a3848f618-release-macos-` | OpenAI_Codex | R12 |
| `aidev-3987572570-735a222908dfbbc043681c469c5ada4208e986f7-pub-release.ym` | OpenAI_Codex | R13 |
| `aidev-4124901376-3b733d914d777685acee80dc626de699e44e34da-release.yml` | OpenAI_Codex | R15 |
| `aidev-3969949090-0d919a9637c447b6f4b872c115ef108e9598bea4-docs.yml` | OpenAI_Codex | R12 |
| `human-ExtractPDF4J_ExtractPDF4J-f08b2b2da8cd-docs-site.yml` | human | R12 |
| `human-cagnulein_qdomyos-zwift-cbe19ab594c7-update-translations.yml` | human | R15 |

## Sample flipped to negative (trusted-owner realignment)

| pair_id | agent | old_rules |
|---|---|---|
| `aidev-3189641151-b3fa304709df7801a10957fe9f22ce9b4cddc919-docker-mcp-pub` | OpenAI_Codex | R06 |
| `aidev-4036411934-c2a38580d5c5322d38d4728d425a46b3694ef68b-bump-personal-` | OpenAI_Codex | R06 |
| `aidev-3145226921-5669d0e7f70ede048faf773f98a192f8d87355e3-docker-publish` | OpenAI_Codex | R06 |
| `aidev-3364889710-299c5cc48db73c074d9e70e10372439aa6630b55-publish-image.` | OpenAI_Codex | R06 |
| `aidev-3969248802-ac807b79abd952ba556eb8bf588c658c7c7bb970-build-containe` | OpenAI_Codex | R06 |
| `aidev-3969248802-ac807b79abd952ba556eb8bf588c658c7c7bb970-reis-stresstes` | OpenAI_Codex | R06 |

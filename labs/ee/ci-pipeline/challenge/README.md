# 🎯 Challenge — Full CI pipeline to build + sign an EE

## ✅ Objective

Write 2 CI pipelines (GitHub Actions + GitLab CI) that build,
scan and sign a production EE. Both files are delivered as a
**skeleton** (with `???`): you write each step.

| File | Expectation |
| --- | --- |
| `.github/workflows/build-ee.yml` | External actions pinned by **40-character SHA**. `permissions: {}` globally, re-broadened in the job (including `id-token: write` for cosign). `persist-credentials: false`. **Trivy** scan with `exit-code: '1'`. **`cosign` signature**. |
| `.gitlab-ci.yml` | 4 stages `build`, `scan`, `push`, `sign`, with one job per stage. |
| `execution-environment.yml` | Delivered. Must declare `version: 3` (builder v3 schema). |

## 🧩 Stuck?

```bash
dsoxlab hint ee-ci-pipeline
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🚀 Launch

The pipeline runs on PR / tag, not locally. Validate at least the
GitHub workflow with `actionlint .github/workflows/build-ee.yml`: pytest
also runs it if the binary is present.

## 📓 Command log

When both pipelines are ready, record in `challenge/solution.sh`
the commands you used (searching SHAs via `gh api`, running `actionlint`).
This log must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/ee/ci-pipeline/challenge/tests/
```

The test validates the **semantics** of both CI files (SHA pinning,
permissions, blocking Trivy, cosign, 4 stages) and runs actionlint if
available.

## 🧹 Reset

```bash
dsoxlab clean ee-ci-pipeline
```

## 💡 Going further

- **Renovate / Dependabot**: auto-update of pinned SHAs (with PRs).
- **Reusable workflows**: factor the EE build across several repos.
- **`cosign` secrets Vault**: prefer the **keyless OIDC** signature
  (no private key to handle).
- **SLSA-3 provenance**: add `actions/attest-build-provenance` for
  the SLSA attestation.

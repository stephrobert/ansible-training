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

## 🧩 Hints

### GitHub Actions skeleton

```yaml
---
name: Build & sign EE

on:
  push:
    tags: ["v*.*.*"]
  pull_request:
    branches: [main]

permissions: {}                            # ← {} mandatory globally

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      id-token: write                      # cosign keyless OIDC

    steps:
      - uses: actions/checkout@???        # 40-char SHA (e.g.: b4ffde...)
        with:
          persist-credentials: false      # ← mandatory

      - uses: redhat-actions/podman-login@???
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - run: ansible-builder build --tag ghcr.io/${{ github.repository }}/ee:${{ github.ref_name }}

      - uses: aquasecurity/trivy-action@???
        with:
          image-ref: ghcr.io/${{ github.repository }}/ee:${{ github.ref_name }}
          severity: CRITICAL,HIGH
          exit-code: '1'                  # ← block if HIGH+ vuln

      - uses: sigstore/cosign-installer@???
      - run: cosign sign --yes ghcr.io/${{ github.repository }}/ee:${{ github.ref_name }}
```

### Pinning an action by SHA

```bash
gh api repos/actions/checkout/git/refs/tags/v4.2.2 --jq .object.sha
# → b4ffde65f46336ab88eb53be808477a3936bae11
# Use in `uses:` instead of @v4 (mutable)
```

### GitLab CI skeleton (4 stages)

```yaml
---
stages:
  - build
  - scan
  - push
  - sign

variables:
  EE_IMAGE: $CI_REGISTRY_IMAGE/ee:$CI_COMMIT_TAG

build:
  stage: build
  ???

scan:
  stage: scan
  ???

push:
  stage: push
  ???

sign:
  stage: sign
  ???
```

> 💡 **Pitfalls**:
>
> - **Pinning by 40-char SHA**: `actions/checkout@b4ffde6...` (not
>   `@v4`). Supply chain security: a tag can be moved, a SHA cannot.
> - **`permissions: {}`** globally, broadened per job with `permissions:
>   { contents: read, packages: write, id-token: write }`. Principle of
>   least privilege.
> - **`persist-credentials: false`** on `actions/checkout`: otherwise the
>   token stays in `.git/config` after checkout (leak risk).
> - **`cosign` keyless**: OIDC signature without a private key. Requires
>   `id-token: write` permission. Simpler than long-lived keys.
> - **Trivy `exit-code: '1'`**: block the pipeline on CRITICAL/HIGH.
>   Without it, the scan is cosmetic.

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

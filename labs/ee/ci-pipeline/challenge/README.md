# Your EE was built by hand, and it is nine months old

## The situation

The custom EE runs everything in production, and it was built on a laptop last
autumn. Since then its base image has collected critical CVEs, nobody rebuilt it
because nobody owns the job, and nobody can prove the image on the registry is
the one that was built: it was pushed from a workstation with a personal token.
An artefact that runs your whole fleet cannot come from someone's afternoon.

Your mission, from the project directory:

1. Build the EE in **CI** instead of on a workstation, so a rebuild is a commit
   away and the CVE clock stops running unattended.
2. **Scan the image and block on it**: a build that finds high or critical
   vulnerabilities must fail the pipeline, not warn in a log nobody reads.
3. **Sign the image** keylessly, so consumers can verify the artefact came from
   your pipeline and not from a workstation, then publish it.
4. Harden the pipeline itself: **pin third-party actions by commit SHA**, keep
   global permissions empty and grant only what each job needs, and leave no
   credentials behind in the checkout.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/exec-playbook/#pipeline-github-actions (in French)

## 🎯 Challenge — Full CI pipeline to build + sign an EE

### ✅ Objective

Write 2 CI pipelines (GitHub Actions + GitLab CI) that build,
scan and sign a production EE. Both files are delivered as a
**skeleton** (with `???`): you write each step.

| File | Expectation |
| --- | --- |
| `.github/workflows/build-ee.yml` | External actions pinned by **40-character SHA**. `permissions: {}` globally, re-broadened in the job (including `id-token: write` for cosign). `persist-credentials: false`. **Trivy** scan with `exit-code: '1'`. **`cosign` signature**. |
| `.gitlab-ci.yml` | 4 stages `build`, `scan`, `push`, `sign`, with one job per stage. |
| `execution-environment.yml` | Delivered. Must declare `version: 3` (builder v3 schema). |

### 🧩 Stuck?

```bash
dsoxlab hint ee-ci-pipeline
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

The pipeline runs on PR / tag, not locally. Validate at least the
GitHub workflow with `actionlint .github/workflows/build-ee.yml`: pytest
also runs it if the binary is present.

### 📓 Command log

When both pipelines are ready, record in `challenge/solution.sh`
the commands you used (searching SHAs via `gh api`, running `actionlint`).
This log must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/ee/ci-pipeline/challenge/tests/
```

The test validates the **semantics** of both CI files (SHA pinning,
permissions, blocking Trivy, cosign, 4 stages) and runs actionlint if
available.

### 🧹 Reset

```bash
dsoxlab clean ee-ci-pipeline
```

### 💡 Going further

- **Renovate / Dependabot**: auto-update of pinned SHAs (with PRs).
- **Reusable workflows**: factor the EE build across several repos.
- **`cosign` secrets Vault**: prefer the **keyless OIDC** signature
  (no private key to handle).
- **SLSA-3 provenance**: add `actions/attest-build-provenance` for
  the SLSA attestation.

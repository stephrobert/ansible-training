# The role is open source now, and strangers will send patches

## The situation

Your `webserver` role is public. The first outside pull request arrives tomorrow,
and you will not run it by hand: you neither trust the code nor have the time,
and nobody wants to be the human who forgot to test one distribution. Worse, a
workflow that clones the repo and runs untrusted code with a writable token is
how a role becomes an attack path. The gate has to be automatic, and it has to
be safe on a contributor's branch.

Your mission, from the project directory:

1. Have every push and pull request go through **two gates**: linting first, then
   the Molecule cycle, so a style failure never burns matrix minutes.
2. Spread the test job across a matrix of **distributions crossed with
   `ansible-core` versions**, running in parallel.
3. Cache the Python dependency install between runs, so the pipeline stays fast
   enough that people actually wait for it.
4. Lock the workflow down: **least-privilege token permissions**, and no
   credentials left behind in the checkout for later steps to reuse.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ci-github-actions/ (in French)

## 🎯 Challenge — Write the GitHub Actions workflow (lint + Molecule matrix)

### ✅ Mission

The `.github/workflows/test.yml` file is delivered **incomplete** (some `???`
and empty jobs). Complete it to get an Ansible role CI compliant with the
expected state below. You are the one writing the workflow: no ready-to-copy
template is provided.

Expected state (this is what pytest checks):

| Requirement | Detail |
| --- | --- |
| 2 jobs | `lint` then `molecule`, chained by `needs:` |
| Lint | `yamllint` and `ansible-lint --profile=production` run in the `lint` job |
| Matrix | `strategy.matrix` with `distro` (at least 2 images) and `ansible` (at least 2 ansible-core versions) |
| Full report | matrix `fail-fast: false` so one failing combination does not cancel the others |
| Supply chain security | all `uses:` actions pinned by 40-character SHA |
| Least privilege | global `permissions:` empty (`{}`), rights granted job by job |
| Credentials | `persist-credentials: false` on each `actions/checkout` |

### 🧩 Stuck?

```bash
dsoxlab hint ci-github-actions
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 📓 Command log

When your workflow is ready, record in `challenge/solution.sh` the
commands you used to build and validate it (for
example the `gh api` and `actionlint` calls). This log, required by the
test harness, must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/ci/github-actions/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ci-github-actions
```

### 💡 Going further

- `zizmor .github/workflows/test.yml`: static security audit of workflows.
- Reusable workflows: share this CI across several roles.
- Dependabot: automatic PRs to keep the pinned SHAs up to date.

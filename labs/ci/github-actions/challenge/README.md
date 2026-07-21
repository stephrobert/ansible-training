# 🎯 Challenge — Write the GitHub Actions workflow (lint + Molecule matrix)

## ✅ Mission

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

## 🧩 Hints

- A tag (`@v4`) can be moved, a SHA cannot. To find a tag's SHA:

  ```bash
  gh api repos/actions/checkout/git/refs/tags/v4.2.2 --jq .object.sha
  ```

- `permissions: {}` at the global level is not enough to build: widen it again
  in each job (`contents: read` at minimum).
- The matrix is declared under `strategy.matrix`, and `fail-fast: false`
  lets all combinations run even if one fails.
- Validate locally with `actionlint .github/workflows/test.yml`: pytest
  runs it too if the binary is present.

## 📓 Command log

When your workflow is ready, record in `challenge/solution.sh` the
commands you used to build and validate it (for
example the `gh api` and `actionlint` calls). This log, required by the
test harness, must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/ci/github-actions/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ci-github-actions
```

## 💡 Going further

- `zizmor .github/workflows/test.yml`: static security audit of workflows.
- Reusable workflows: share this CI across several roles.
- Dependabot: automatic PRs to keep the pinned SHAs up to date.

# The company runs GitLab, and a release just shipped from a branch

## The situation

The team's roles moved to the internal GitLab, and the old GitHub workflow does
not translate. The first attempt made things worse: the publish job had no
condition on it, so a merge to a feature branch pushed a release to Galaxy that
nobody had approved. Publishing is not a step in a test pipeline. It is what
happens when, and only when, someone deliberately tags a version.

Your mission, from the project directory:

1. Lay the pipeline out in **three stages**, lint then test then release, so a
   job never runs before the one that could have stopped it.
2. Spread the test stage over a **distribution and version matrix**, in parallel,
   and cache the Python dependencies between runs.
3. Gate the release job so it triggers **only on a Git tag**, never on a branch
   push and never on a merge request.
4. Have the release job publish to Galaxy with its token, and keep that token out
   of every other stage.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ci-gitlab/ (in French)

## 🎯 Challenge — Write the GitLab CI pipeline (lint + matrix + release)

### ✅ Mission

The `.gitlab-ci.yml` file is delivered **incomplete** (some `???` and missing
jobs). Complete it to get the expected pipeline: you are the one
writing each job, no ready-to-copy template is provided.

Expected state (this is what pytest checks):

| Requirement | Detail |
| --- | --- |
| Stages | `lint`, `test` and `release` declared in `stages:` |
| Job `ansible-lint` | stage `lint`, runs `yamllint` and `ansible-lint --profile=production` |
| Job `molecule-test` | stage `test`, `needs: ["ansible-lint"]`, `parallel:matrix` of at least 3 DISTRO x ANSIBLE_VERSION combinations |
| Job `release` | stage `release`, `rules:` with a condition on `$CI_COMMIT_TAG` (triggered only on tag) |
| Secrets | no token or plaintext password in the file |

### 🧩 Stuck?

```bash
dsoxlab hint ci-gitlab
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 📓 Command log

When your pipeline is ready, record in `challenge/solution.sh` the
commands used to validate it locally (for example
`python3 -c "import yaml; yaml.safe_load(open('.gitlab-ci.yml'))"` or a
`gitlab-ci-local` run). This log must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/ci/gitlab/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ci-gitlab
```

### 💡 Going further

- `gitlab-ci-local`: run the pipeline on your machine before pushing.
- `include:`: factor this pipeline into a CI templates repo.
- Pipeline and coverage badges in the role's README.

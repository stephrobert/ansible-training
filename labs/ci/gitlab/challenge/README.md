# 🎯 Challenge — Write the GitLab CI pipeline (lint + matrix + release)

## ✅ Mission

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

## 🧩 Hints

- The GitLab matrix is declared like this:

  ```yaml
  parallel:
    matrix:
      - DISTRO: ...
        ANSIBLE_VERSION: "..."
  ```

  Each list entry is a combination (or a cartesian product if
  a key holds a list).

- `needs: ["ansible-lint"]` short-circuits the stage order and documents the
  real dependency.
- For the release, the canonical pattern is:

  ```yaml
  rules:
    - if: $CI_COMMIT_TAG
  ```

- The Galaxy token NEVER goes here: Settings, CI/CD, Variables
  (masked + protected), then reference `$GALAXY_API_KEY` in the script.

## 📓 Command log

When your pipeline is ready, record in `challenge/solution.sh` the
commands used to validate it locally (for example
`python3 -c "import yaml; yaml.safe_load(open('.gitlab-ci.yml'))"` or a
`gitlab-ci-local` run). This log must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/ci/gitlab/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ci-gitlab
```

## 💡 Going further

- `gitlab-ci-local`: run the pipeline on your machine before pushing.
- `include:`: factor this pipeline into a CI templates repo.
- Pipeline and coverage badges in the role's README.

# Lab 70 — CI/CD: GitLab CI

> 💡 **Landing directly on this lab without having done the previous ones?**
> Local prerequisite: none. To run it: a GitLab project (SaaS
> instance gitlab.com or self-hosted).

## 🧠 Recap

🔗 [**Ansible CI with GitLab CI**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ci-gitlab/)

GitLab CI is the **GitLab equivalent** of GitHub Actions:

| GitHub Actions | GitLab CI |
| --- | --- |
| `.github/workflows/test.yml` | `.gitlab-ci.yml` (at the root) |
| `jobs:` | `stages:` + jobs |
| `strategy.matrix:` | `parallel:matrix:` |
| `actions/checkout@v4` | (auto, already cloned) |
| `runs-on: ubuntu-latest` | `image:` (any Docker image) |

GitLab CI has a **key advantage** over GitHub Actions: **native
Docker-in-Docker**, useful for Molecule + Podman/Docker. Simpler to configure.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Write `.gitlab-ci.yml` with **stages**: lint, test, release.
2. Use **`parallel:matrix:`** for multi-distro / multi-version.
3. Declare **`rules:`**: tests on PR, release only on tag.
4. pip cache via stage-level **`cache:`**.
5. Store a **release** job to Galaxy (only on git tag).

## 🔧 Preparation

No local installation.

## ⚙️ Layout

```text
labs/ci/gitlab/
├── README.md
├── .gitlab-ci.yml        ← full pipeline
└── roles/webserver/
```

## 📚 Exercise 1 — `.gitlab-ci.yml` skeleton

```yaml
---
stages:
  - lint
  - test
  - release

default:
  image: python:3.12-slim
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - .cache/pip

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  PYTHONUNBUFFERED: "1"

ansible-lint:
  stage: lint
  before_script:
    - pip install ansible-lint yamllint
  script:
    - yamllint .
    - ansible-lint --profile production
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"

molecule-test:
  stage: test
  needs: [ansible-lint]
  image: quay.io/ansible/community-ansible-dev-tools:latest
  parallel:
    matrix:
      - DISTRO:
          - quay.io/centos/centos:stream10
          - docker.io/library/debian:12
          - docker.io/library/ubuntu:24.04
        ANSIBLE_VERSION: ["2.16", "2.17", "2.18"]
  script:
    - pip install ansible-core==${ANSIBLE_VERSION}.*
    - molecule test
  variables:
    MOLECULE_DISTRO: $DISTRO

galaxy-release:
  stage: release
  rules:
    - if: $CI_COMMIT_TAG
  image: python:3.12-slim
  before_script:
    - pip install ansible-core
  script:
    - ansible-galaxy role import --token $GALAXY_TOKEN
        --branch $CI_COMMIT_REF_NAME
        $CI_PROJECT_NAMESPACE $CI_PROJECT_NAME
```

🔍 **Observation**:

- **3 stages**: lint → test → release.
- **`needs:`**: `molecule-test` runs only if `ansible-lint` passes.
- **`parallel:matrix:`**: 9 jobs (3 distros × 3 versions).
- **`rules:`**: `galaxy-release` runs **only on a Git tag**.

## 📚 Exercise 2 — `rules:` (when to run)

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"     # MR opened
  - if: $CI_COMMIT_BRANCH == "main"                       # push on main
  - if: $CI_COMMIT_TAG                                    # git tag (release)
```

🔍 **Observation**: `rules:` replace the old `only:` / `except:`. More
expressive.

## 📚 Exercise 3 — pip cache

```yaml
default:
  cache:
    key: ${CI_COMMIT_REF_SLUG}     # cache per branch
    paths:
      - .cache/pip
```

🔍 **Observation**: cache **per branch**. A PR has its own cache,
does not pollute main.

## 📚 Exercise 4 — Protected variables (Galaxy token)

In the GitLab UI: Settings → CI/CD → Variables:

```text
GALAXY_TOKEN = <Ansible Galaxy token>
Protected: ✓     (only on protected branches/tags)
Masked: ✓        (hidden in the logs)
```

🔍 **Observation**: **never** put a token in plaintext in
`.gitlab-ci.yml`. Always via CI/CD variables.

## 📚 Exercise 5 — `ansible-galaxy role import`

```yaml
script:
  - ansible-galaxy role import --token $GALAXY_TOKEN
      --branch $CI_COMMIT_REF_NAME
      $CI_PROJECT_NAMESPACE $CI_PROJECT_NAME
```

🔍 **Observation**: the Galaxy import from GitHub/GitLab is **automatic**:
no need to upload a .tar.gz. Galaxy clones the repo at the specified tag.

## 🔍 Observations to note

- **GitLab CI = GitHub Actions** at heart, different syntax.
- **`parallel:matrix:`** simplifies multi-jobs.
- **`rules:`** = maximum expressiveness (regex on branch, tag, MR…).
- **Masked + protected CI/CD variables** = security standard.
- **Self-hosted GitLab**: if you have your own instance, unlimited free
  runners.

## 🤔 Reflection questions

1. How would you adapt your solution if the target went from **1 host** to a
   fleet of **50 servers**? Which parameters (`forks`, `serial`, `strategy`)
   would you need to tune to keep acceptable execution times?

2. Which alternative Ansible modules could you have used to reach the same
   result? What are their trade-offs (guaranteed idempotence, performance,
   external collection dependency)?

3. If a playbook step fails mid-run, what is the impact on the hosts already
   processed? How do you make the scenario resumable (`block/rescue/always`,
   `--start-at-task`, `serial`)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md).

## 💡 Going further

- **`include:`**: factor the pipeline into a `.gitlab-ci-template.yml`
  shared across several roles.
- **GitLab Pages**: auto-publish the doc generated by `ansible-doc -t role`
  on GitLab Pages.
- **GitLab CI Runner Kubernetes**: runners that scale automatically
  on K8s.
- **Comparison**: if your role lives on GitHub but you want to
  use GitLab CI, set up a mirror.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/ci/gitlab/
```

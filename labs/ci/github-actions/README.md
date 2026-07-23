# Lab 69 — CI/CD: GitHub Actions

> 💡 **Landing directly on this lab without having done the previous ones?**
> Local prerequisite: none (you just write a YAML workflow). To run it: a GitHub
> account + a fork of your role.

## 🧠 Recap

🔗 [**Ansible CI with GitHub Actions**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ci-github-actions/)

A **complete** CI for an Ansible role orchestrates, on every PR:

```text
1. Lint (ansible-lint --profile production + yamllint)
2. Molecule test (matrix OS × Ansible versions)
3. (optional) Publish to Galaxy on git tag
```

GitHub Actions is free for public repos, ideal for open source roles.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Write `.github/workflows/test.yml` with **2 jobs** (lint + molecule).
2. Use **`strategy.matrix`** to test N distros × M Ansible versions
   **in parallel**.
3. Cache `pip install` between runs with **`actions/setup-python@83679a892e2d95755f2dac6acb0bfd1e9ac5d548 # v6.1.0`**.
4. Configure **minimal permissions** (`permissions: {}`).
5. Disable `persist-credentials: false` on `actions/checkout` (security).

## 🔧 Preparation

No local installation. Optional: `act` to run GitHub Actions workflows locally
(debug).

## ⚙️ Layout

```text
labs/ci/github-actions/
├── README.md
├── requirements.yml                    ← collections + roles
├── roles/webserver/
└── .github/
    └── workflows/
        └── test.yml                    ← full CI workflow
```

## 📚 Exercise 1 — Workflow skeleton

```yaml
---
name: Test webserver role

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: "0 6 * * 1"     # Monday morning (anti-rot)

permissions: {}             # least privilege: grant per job, only what it needs

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
        with:
          persist-credentials: false      # security

      - uses: actions/setup-python@83679a892e2d95755f2dac6acb0bfd1e9ac5d548 # v6.1.0
        with:
          python-version: "3.12"
          cache: pip

      - run: pip install ansible-lint yamllint
      - run: yamllint .
      - run: ansible-lint --profile production

  molecule:
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      fail-fast: false
      matrix:
        distro:
          - quay.io/centos/centos:stream10
          - docker.io/library/debian:12
          - docker.io/library/ubuntu:24.04
        ansible: ["2.16", "2.17", "2.18"]

    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
        with:
          persist-credentials: false

      - uses: actions/setup-python@83679a892e2d95755f2dac6acb0bfd1e9ac5d548 # v6.1.0
        with:
          python-version: "3.12"
          cache: pip

      - run: |
          pip install molecule molecule-plugins[podman]
          pip install ansible-core>=${{ matrix.ansible }},<$(echo ${{ matrix.ansible }} | awk -F. '{print $1"."$2+1}')

      - run: molecule test
        env:
          MOLECULE_DISTRO: ${{ matrix.distro }}
```

🔍 **Observation**:

- **`needs: lint`**: the `molecule` job runs only if `lint` passes.
- **`fail-fast: false`**: if a combination fails, we continue the others to get
  a complete report.
- **`matrix.distro × matrix.ansible`** = **9 jobs in parallel**.

## 📚 Exercise 2 — Minimal permissions

```yaml
permissions: {}
# OR more precise:
permissions:
  contents: read
  pull-requests: write       # only if we comment the PR
```

🔍 **Observation**: by default, `GITHUB_TOKEN` has a lot of rights. In
production, we **reduce to the strict minimum** to limit the blast radius if a
workflow is compromised.

## 📚 Exercise 3 — `persist-credentials: false`

```yaml
- uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
  with:
    persist-credentials: false
```

🔍 **Observation**: by default, `actions/checkout` leaves the `GITHUB_TOKEN`
accessible on the runner's filesystem. If a malicious dependency exfiltrates it,
it is game over. Disable it unless you explicitly need it (to push an auto
commit for example).

## 📚 Exercise 4 — pip cache

```yaml
- uses: actions/setup-python@83679a892e2d95755f2dac6acb0bfd1e9ac5d548 # v6.1.0
  with:
    python-version: "3.12"
    cache: pip
```

🔍 **Observation**: without cache, each run reinstalls ~50 pip packages (~30 s).
With cache, it is ~5 s. On 9 matrix jobs, that changes the total CI duration.

## 📚 Exercise 5 — Schedule (anti-rot)

```yaml
on:
  schedule:
    - cron: "0 6 * * 1"     # Monday morning
```

🔍 **Observation**: a role can **break** without touching the code (Ansible
upstream changes, distro upgrade). Running the CI weekly detects silent
regressions.

## 🔍 Observations to note

- **`needs:`** chains the jobs (lint → molecule).
- **`strategy.matrix`** = free parallelization. Multi-distro × multi-version
  in a few lines of YAML.
- **Minimal permissions** + **`persist-credentials: false`** =
  defense in depth.
- **`schedule`** = detect silent regressions (anti-rot).
- **GitHub Actions is free** on public repos. On private repos:
  2000 free minutes/month, then billed.

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

- **`act`** (local): `act -W .github/workflows/test.yml` runs the workflow on
  your machine.
- **Reusable workflows**: `uses: org/.github/workflows/ansible-test.yml@main`
  to share across several roles.
- **Dependabot**: auto-PR to update action versions
  (it bumps the pinned SHA **and** its `# vX.Y.Z` comment, so pinning stays maintainable).
- **GitGuardian / TruffleHog**: add a secret scanning job on top of pre-commit.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/ci/github-actions/
```

# Lab 68 — `ansible-lint --profile production` + pre-commit

> 💡 **Landing directly on this lab without having done the previous ones?**
> Prerequisites: `pipx install ansible-lint pre-commit yamllint`.

## 🧠 Recap

🔗 [**ansible-lint in production mode**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ansible-lint-production-profile/)

`ansible-lint` has **6 progressive profiles**:

| Profile | Level | Use case |
| --- | --- | --- |
| `min` | Bare minimum | Legacy code, you just want to avoid the worst |
| `basic` | Light | Learning |
| `moderate` | Moderate | Work in progress |
| `safety` | Security | Audit |
| `shared` | Shared roles | Galaxy |
| **`production`** | **Fully strict** | **Code shipped to prod** |

The **`production`** profile is what the **RHCE 2026** expects. It checks:

- Mandatory FQCN (`ansible.builtin.copy`)
- `name:` on every task
- No `command:`/`shell:` when a dedicated module exists
- Idempotence respected (no broken `changed_when`)
- Complete `meta/main.yml` (galaxy_info, platforms, license, min version)
- No deprecated modules
- ...

And you **automate** it with **pre-commit**: a git hook that runs
`ansible-lint` on every commit. Impossible to push non-compliant code.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Configure an `.ansible-lint` file with `profile: production`.
2. Configure a strict `.yamllint` (forbid `yes`/`no`, long lines, etc.).
3. Write a `.pre-commit-config.yaml` that runs lint + yamllint on every
   commit.
4. Enable a hook that **blocks secret leaks** (private keys).
5. Understand the effect on the CI: if pre-commit passes locally, the CI
   passes too.

## 🔧 Preparation

```bash
pipx install ansible-lint pre-commit
pipx inject ansible-lint yamllint
```

## ⚙️ Tree layout

```text
labs/tests/ansible-lint-production/
├── README.md
├── .ansible-lint                 ← profile: production
├── .yamllint                     ← truthy: only true/false
├── .pre-commit-config.yaml       ← hooks ansible-lint + yamllint + secrets
└── roles/webserver/
```

## 📚 Exercise 1 — `.ansible-lint`

```yaml
---
profile: production
strict: true

# Targeted exclusions
exclude_paths:
  - .cache/
  - .pytest_cache/
  - .tox/

# Enable all rules
enable_list:
  - fqcn-builtins
  - no-handler
  - no-relative-paths
  - no-same-owner
```

🔍 **Observation**: `profile: production` enables **~50 rules**. You can
disable some via `skip_list:` but that is a warning sign.

## 📚 Exercise 2 — `.yamllint`

```yaml
---
extends: default

rules:
  line-length:
    max: 120
  truthy:
    allowed-values: ['true', 'false']    # forbids yes/no/on/off
    check-keys: false
  comments:
    min-spaces-from-content: 1
  braces:
    max-spaces-inside: 1
```

🔍 **Observation**: `truthy: only true/false` is crucial. Strict YAML 1.2
treats `yes` as a string, not a boolean. A source of silent bugs.

## 📚 Exercise 3 — `.pre-commit-config.yaml`

```yaml
---
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: detect-private-key       # ← blocks SSH/TLS key leaks
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/adrienverge/yamllint
    rev: v1.35.1
    hooks:
      - id: yamllint
        args: ['--strict']

  - repo: https://github.com/ansible/ansible-lint
    rev: v26.6.0
    hooks:
      - id: ansible-lint
        args: ['--profile=production']
```

🔍 **Observation**:

- **`detect-private-key`**: rejects commits that contain
  `BEGIN PRIVATE KEY` (SSH/TLS key). Essential.
- **`--strict`** on yamllint: **error** (not warning) on violated rules.
- **`--profile=production`** on ansible-lint: the strictest level.

## 📚 Exercise 4 — Enable pre-commit

```bash
cd labs/tests/ansible-lint-production
pre-commit install      # installs the .git/hooks/pre-commit hook
pre-commit run --all-files   # run manually on all files
```

🔍 From now on, **every `git commit`** will go through these hooks. If one
fails, the commit is aborted.

## 📚 Exercise 5 — Demonstrate a block

Modify a role task to make it non-compliant:

```yaml
- name: Mauvais exemple
  copy:                                   # ← missing FQCN (anti-pattern)
    src: foo
    dest: /tmp/foo
    mode: 0644                            # ← unquoted (anti-pattern)
```

```bash
git add .
git commit -m "test"
```

🔍 Expected output:

```text
ansible-lint.....................................FAILED
- fqcn[action-core]: Use FQCN for builtin module actions
- yaml[truthy]: Truthy value should be one of [false, true]
```

The commit is **blocked**. You must fix it before you can push.

## 🔍 Observations to note

- **`profile: production`** = **RHCE 2026 standard**. Use it starting in
  the CI.
- **`pre-commit install`** once is enough: the hook persists in
  `.git/hooks/`.
- **`detect-private-key`**: an SSH/TLS key leak is one of the most frequent
  incidents in open source. A mandatory hook.
- **`yamllint truthy: [true, false]`**: avoids YAML 1.1 vs 1.2 bugs.
- **Redundant CI**: the CI must also run `pre-commit run --all-files` to
  block external contributions that would not have the local hook.

## 🤔 Reflection questions

1. How would you adapt your solution if the target went from **1 host** to
   a fleet of **50 servers**? Which parameters (`forks`, `serial`, `strategy`)
   would you need to tune to keep execution times acceptable?

2. Which alternative Ansible modules could you have used to reach the same
   result? What are their trade-offs (guaranteed idempotence, performance,
   external collection dependencies)?

3. If a playbook step fails mid-run, what is the impact on the hosts already
   processed? How do you make the scenario resumable
   (`block/rescue/always`, `--start-at-task`, `serial`)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md).

## 💡 Going further

- **`ansible-lint --write`**: auto-fixes simple anti-patterns
  (FQCN, quoted mode).
- **`pre-commit autoupdate`**: updates the pinned hook versions.
- **GitHub Actions**: a job that runs `pre-commit run --all-files`,
  redundant with local but protects against external contributors.
- **Custom rules**: `ansible-lint` lets you write your own company rules
  (forbid a specific module, etc.).

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint --profile production labs/tests/ansible-lint-production/
```

# Lab 76 — Versioning & publishing a role (semver, Git tags, Galaxy)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Prerequisite: Ansible installed, `git` configured. No VMs needed.

## 🧠 Recap

🔗 [**Versioning and publishing an Ansible role**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/versionner-publier/)

A **published** Ansible role must be:

- **Versioned** in SemVer (`MAJOR.MINOR.PATCH`).
- Accompanied by a **`CHANGELOG.md`** in
  [Keep a Changelog](https://keepachangelog.com/) format (Added /
  Changed / Fixed / Deprecated / Removed / Security sections).
- **Tagged** in Git (`git tag v1.2.0`).
- **Pinnable** from a consuming `requirements.yml`.

This is the culmination of the lifecycle: **write → test → publish →
consume pinned**.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Apply **SemVer**: when to bump MAJOR / MINOR / PATCH.
2. Write a **`CHANGELOG.md`** in Keep a Changelog format.
3. **Tag** a Git release with an annotated message.
4. **Publish** to Galaxy via GitHub webhook or via CLI.
5. Document **pinning** on the consumer side.
6. Automate the release via **CI/CD** (tag → publish workflow).

## 🔧 Preparation

```bash
git --version
ansible-galaxy --version
```

## ⚙️ Directory tree

```text
labs/galaxy/versionner-publier/
├── README.md
├── CHANGELOG.md           ← Keep a Changelog with ≥ 2 versions
├── PUBLISH.md             ← publication procedure
└── roles/webserver/        ← example role to publish
```

## 📚 Exercise 1 — Read `CHANGELOG.md`

```markdown
# Changelog — rôle webserver

## [1.2.0] - 2026-04-26

### Added
- Support multi-distribution (RHEL, AlmaLinux, Debian via vars/<os_family>.yml)
- Variable `webserver_worker_processes` configurable
- Validation argument_specs.yml

### Changed
- Module `package` (agnostique) au lieu de `dnf` direct

### Fixed
- Idempotence handlers (Reload nginx déclenché 2× résolu)
```

🔍 **Observation**: 3 distinct sections (`Added`, `Changed`, `Fixed`)
classify the changes. **Without a `CHANGELOG.md`**, the user of an
upgrade does not know whether it is a breaking change.

## 📚 Exercise 2 — SemVer rules

| Bump | When | Example |
| --- | --- | --- |
| **MAJOR** (1.x.x → 2.0.0) | Breaking change: variable removed/renamed, structure broken | Rename `nginx_listen` → `webserver_listen` |
| **MINOR** (1.0.x → 1.1.0) | New **backward-compatible** feature | Add `webserver_workers` (default = old behavior) |
| **PATCH** (1.0.0 → 1.0.1) | Bugfix without API change | Fix a handler that triggers twice |

🔍 **Golden rule**: **`1.0.0 → 2.0.0`** signals to consumers that they
must **read the CHANGELOG** and migrate their code.

## 📚 Exercise 3 — Tag a release

```bash
# 1. Make sure the tests pass
molecule test
ansible-lint --profile production roles/webserver/

# 2. Update CHANGELOG.md (add the [1.2.0] section)
$EDITOR CHANGELOG.md

# 3. Commit + annotated tag
git add CHANGELOG.md
git commit -m "release: v1.2.0"
git tag -a v1.2.0 -m "Release v1.2.0 — Multi-distro support"

# 4. Push tag
git push origin main --tags
```

🔍 **Observation**: `git tag -a` (annotated) **>>** `git tag` (lightweight):
the annotated tag contains a message + author + date, which is what
Galaxy reads for the release notes.

## 📚 Exercise 4 — Galaxy publication

### Method 1 — GitHub webhook (roles, recommended)

1. On https://galaxy.ansible.com → **My Content → Add Content → Import
   Role from GitHub**.
2. Select `<user>/ansible-role-webserver`.
3. On each **new SemVer tag**, Galaxy triggers an automatic import.

### Method 2 — CLI (collections, mandatory)

```bash
cd path/to/collection/
ansible-galaxy collection build           # → user-collection-1.2.0.tar.gz
ansible-galaxy collection publish \
  user-collection-1.2.0.tar.gz \
  --api-key=$GALAXY_TOKEN
```

🔍 **Observation**: `--api-key` (and not `--token`) accepts a token
generated on https://galaxy.ansible.com/me/preferences.

## 📚 Exercise 5 — Read `PUBLISH.md`

The shipped file explains:

- The **Git workflow** (test → CHANGELOG → commit → tag → push).
- The **2 methods** of publication (webhook vs CLI).
- The **consumer pinning** in `requirements.yml`.
- The automated **CI/CD** (GitHub Actions workflow on tag).

## 📚 Exercise 6 — Pinning on the consumer side

```yaml
# requirements.yml of another project that consumes your role
roles:
  - src: stephrobert.webserver
    version: 1.2.0          # exact match production

  # Or SemVer range
  - src: stephrobert.webserver
    version: ">=1.2.0,<2.0.0"
```

🔍 **Observation**: the `>=1.2.0,<2.0.0` range allows patch + minor
(backward compat) but blocks the MAJOR jump. This is the **pragmatic prod**
pattern.

## 🔍 Observations to note

- **SemVer + CHANGELOG** = a **stability** contract with your
  users.
- **Annotated tag** (`git tag -a`) > lightweight tag for Galaxy.
- **Galaxy webhook** is the **lazy efficient** option for roles.
- **Collections** (publication) = mandatorily via CLI + token.
- **Automated releases** via CI/CD: tag → workflow → Galaxy publish.

## 🤔 Reflection questions

1. You rename `nginx_user` → `webserver_user`. Which SemVer bump?
   How do you migrate users without breaking them?

2. You want to **roll back** a release. How do you do it on
   Galaxy? (Hint: there is no really clean delete.)

3. Difference between publishing a **role** (1 `meta/main.yml` file) and a
   **collection** (`galaxy.yml` + `.tar.gz`)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md).

## 💡 Going further

- **`towncrier`**: automatic CHANGELOG generator (Python, but
  applicable to Ansible).
- **`semantic-release`**: tag + CHANGELOG + publish automation.
- **GitHub Releases**: auto-generation of release notes from the
  CHANGELOG.
- **Pre-release SemVer**: `1.2.0-rc1`, `1.2.0-beta.1` (accepted by Galaxy).

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/galaxy/versionner-publier/
```

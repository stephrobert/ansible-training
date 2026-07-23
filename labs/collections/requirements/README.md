# Lab 94 — Complete `requirements.yml` (Galaxy + Git + GPG signatures)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root.

## 🧠 Recap

🔗 [**Complete `requirements.yml`**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/requirements-yml/)

A mature Ansible project **versions its dependencies** in a single **`requirements.yml`** file. It lists the **collections** and **roles** used, their **source** (Galaxy, Git, tarball URL, local path), their **pinned version** (strict semver), and optionally their **GPG signatures** for integrity verification.

**Why it is critical in 2026**:
- **Reproducible builds** of Execution Environments depend on `requirements.yml`.
- The **supply-chain scan** (Trivy, cosign, signatures) targets this file.
- A project without pinning **drifts** over the days and breaks in prod without warning.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Write a **`requirements.yml`** with **4 different sources** (Galaxy, Git, URL, local path).
2. **Pin** each version strictly (semver `version: "X.Y.Z"`).
3. Install all the collections with **`ansible-galaxy collection install -r`**.
4. Verify integrity with **`ansible-galaxy collection verify`**.
5. Understand the detached **GPG signatures** (`signatures:` in `requirements.yml`).
6. Configure **`ansible.cfg [galaxy]`** to target **several servers** (Galaxy + private Hub).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping
ansible-galaxy --version
mkdir -p labs/collections/requirements/local_collections
rm -rf labs/collections/requirements/.collections-cache
```

## ⚙️ Target layout

```text
labs/collections/requirements/
├── README.md                       ← this file (guided tutorial)
└── challenge/
    ├── README.md                   ← challenge brief with skeleton
    └── tests/
        └── test_requirements.py
```

The learner writes `requirements.yml`, `lab.yml`, and `challenge/solution.yml` themselves.

## 📚 Exercise 1 — Galaxy source with strict pinning

Create `requirements.yml`:

```yaml
---
collections:
  # Default Galaxy source (galaxy.ansible.com)
  - name: ansible.posix
    version: "2.0.0"

  - name: community.general
    version: "10.5.0"

  - name: kubernetes.core
    version: "5.1.1"
```

```bash
ansible-galaxy collection install \
  -r labs/collections/requirements/requirements.yml \
  -p labs/collections/requirements/local_collections \
  --force
```

🔍 **Observation**: **`-p`** forces the installation into a path **local to the project** (not in `~/.ansible/`). Allows **isolation** between projects and **reproducibility** (the path is versioned).

## 📚 Exercise 2 — Git source with tag, branch or SHA

Add to `requirements.yml`:

```yaml
collections:
  - name: https://github.com/ansible-collections/community.docker.git
    type: git
    version: "4.0.0"           # Git tag
```

Accepted variants in **`version:`**:

| Format | Example | Use case |
|--------|---------|-------------|
| Tag | `version: v1.2.3` | Stable production (recommended) |
| Branch | `version: main` | Fast dev (discouraged in prod) |
| SHA40 | `version: abc1234...` | Absolute reproducibility |

🔍 **Observation**: **Git source** is useful for collections **not published on Galaxy** (private company ones, internal fork, ongoing contributions). In prod, **always** pin by **tag** or **SHA**, never by branch.

## 📚 Exercise 3 — Tarball URL source

```yaml
collections:
  - name: https://example.com/dist/acme-webapp-1.4.2.tar.gz
    type: url
```

🔍 **Observation**: useful for **internal airgap distributions** where Galaxy is not reachable. Pre-build the tarball with `ansible-galaxy collection build`, put it on a local HTTP server, point to it here.

## 📚 Exercise 4 — Local path source (dev)

```yaml
collections:
  - name: ~/dev/acme.webapp
    type: dir
```

🔍 **Observation**: **dev mode** where you work on your collection locally. Change immediately visible: no need to rebuild/reinstall on each change. To be removed in prod (non-portable absolute path).

## 📚 Exercise 5 — Run the installation

```bash
ansible-galaxy collection install \
  -r labs/collections/requirements/requirements.yml \
  -p labs/collections/requirements/local_collections \
  --force
```

Typical output:

```text
Starting galaxy collection install process
Process install dependency map
Starting collection install process
Downloading https://galaxy.ansible.com/.../ansible-posix-2.0.0.tar.gz to ...
Installing 'ansible.posix:2.0.0' to '.../local_collections/ansible_collections/ansible/posix'
Cloning into 'community.docker'...
...
ansible.posix:2.0.0 was installed successfully
community.general:10.5.0 was installed successfully
community.docker:4.0.0 was installed successfully
```

🔍 **Observation**: `--force` reinstalls **even if the version is already present**. Useful in dev to make sure you have the pinned version. In CI, **omit** `--force` (faster).

## 📚 Exercise 6 — `ANSIBLE_COLLECTIONS_PATH`

Once installed locally, you must tell Ansible where to look:

```bash
export ANSIBLE_COLLECTIONS_PATH=labs/collections/requirements/local_collections
ansible-galaxy collection list -p labs/collections/requirements/local_collections
```

Or in `ansible.cfg`:

```ini
[defaults]
collections_path = labs/collections/requirements/local_collections
```

🔍 **Observation**: the env variable **`ANSIBLE_COLLECTIONS_PATH`** is a `:` separator (like `$PATH`). Allows chaining several paths (system + project) with priority.

## 📚 Exercise 7 — Integrity verification (`verify`)

```bash
ansible-galaxy collection verify \
  -r labs/collections/requirements/requirements.yml \
  -p labs/collections/requirements/local_collections
```

Output:

```text
Verifying 'ansible.posix:2.0.0'.
Found ansible.posix at /home/.../local_collections/ansible_collections/ansible/posix
Successfully verified that checksums for 'ansible.posix:2.0.0' match the remote collection
```

🔍 **Observation**: `verify` compares the **checksums** of the local files with those of the server. **Detects a corruption** (disk, manual modification) or a **substitution** (supply-chain attack). To automate in CI.

## 📚 Exercise 8 — Detached GPG signatures

For **Red Hat certified** collections or private forks, you add signatures:

```yaml
collections:
  - name: community.general
    version: "10.5.0"
    signatures:
      - https://galaxy.ansible.com/api/v3/.../detached_signature.asc
      - file:///etc/ansible/sigs/community-general-10.5.0.asc
```

```bash
ansible-galaxy collection install \
  -r requirements.yml \
  --keyring /etc/ansible/trustedkeys.gpg
```

Associated variables:

| Variable | Effect |
|----------|-------|
| `GALAXY_REQUIRED_VALID_SIGNATURE_COUNT` | Minimum number of valid signatures (`+1`, `+all`) |
| `GALAXY_DISABLE_GPG_VERIFY` | `1` disables (debug only) |
| `--keyring` | Path to the trusted GPG keyring |

🔍 **Observation**: requires **`ansible-core ≥ 2.13`**. Without `--keyring`, the install **fails** if signatures are declared. Essential pattern for **signed airgap** (offline verify with `--offline`).

## 🔍 Observations to note

- **`requirements.yml`** centralizes all the Ansible dependencies.
- **4 sources**: Galaxy (default), `type: git`, `type: url`, `type: dir`.
- **Strict pinning** by **tag** or **SHA**: never by branch in prod.
- **`-p <path>`** isolates the collections at the project level.
- **`ansible-galaxy collection verify`** detects corruptions and substitutions.
- **GPG signatures** via `signatures:` + `--keyring` for the supply-chain chain.

## 🤔 Reflection questions

1. What is the risk of **`type: git, version: main`** in production?
2. How do you update the pinned versions **automatically**? (Hint: Renovate / Dependabot).
3. What is **`build_ignore:`** used for in `galaxy.yml`? What is the equivalent on the `requirements.yml` side?
4. Why is a **private registry** (Galaxy NG / Automation Hub) preferable to Git for internal forks?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md): write a `requirements.yml` that combines **3 sources** (Galaxy + Git + URL) with strict pinning, install it via Ansible, and deposit the list of collections on `db1.lab`.

## 💡 Going further

- **Lab 95**: create **your own collection** (init + structure + galaxy.yml).
- **Lab 96**: CI matrix pipeline ansible-core × Python.
- **Renovate** to auto-bump the pinned versions.
- **Galaxy NG**: deploy a local private Automation Hub.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/collections/requirements/lab.yml
ansible-lint --profile production labs/collections/requirements/challenge/solution.yml
```

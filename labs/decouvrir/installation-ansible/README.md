# Lab 02 — Installing Ansible (checking your control node)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root (see
> [root README](../../../README.md#-démarrage-rapide) for the details).

## 🧠 Recap

🔗 [**Installing Ansible: pipx, mise, dnf, Execution Environment**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/installation-ansible/)

Before writing a single playbook, you need **a control node that works**: Ansible installed, the right binaries in the `PATH`, the main collections present. This lab requires **nothing to write**: you are going to **inspect** your installation and learn to diagnose a misconfigured node.

The blog page presents the **5 installation methods** recommended in 2026:

| Method | For whom | Typical command |
| --- | --- | --- |
| **`pipx`** | Personal machine (recommended) | `pipx install --include-deps ansible` |
| **`dnf` / `apt`** | Stable distro | `sudo dnf install ansible` |
| **`mise`** | Several versions side by side | `mise use ansible@latest` |
| **`uv tool install`** | Modern alternative to pipx | `uv tool install ansible` |
| **Execution Environment** | Total reproducibility (RHCE 2026 target) | `ansible-navigator run …` |

You do **not** need all 5 on your machine: a single one is enough. But you must know which one you use: it determines **where** Ansible is installed and **how** to update it.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Read `ansible --version` and identify your **installation method**.
2. Check that the **8 standard** Ansible binaries are in your `PATH`.
3. Measure how many **modules** are accessible via `ansible-doc`.
4. Confirm the presence of the repo's **key collections** (`ansible.posix`, `community.general`, `community.libvirt`).
5. Run the lab's **automated verification** via `dsoxlab run <id-du-lab>`.

## 🔧 Preparation

No VM needed: all the commands run **on your workstation** (the control node). Move to the repo root:

```bash
cd $ANSIBLE_TRAINING
```

> 💡 **If Ansible is not installed at all**: the blog page cites `pipx install --include-deps ansible` as a quick install, or `mise install` at the repo root which installs the entire chain (Ansible + lint tools + libvirt). Run it **before** continuing.

## 📚 Exercise 1 — Which Ansible version do you have?

```bash
ansible --version
```

Typical output:

```text
ansible [core 2.20.1]
  config file = /home/<vous>/Projets/ansible-training/ansible.cfg
  configured module search path = ['/home/<vous>/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /home/<vous>/.local/share/pipx/venvs/ansible/lib/python3.12/site-packages/ansible
  ansible collection location = /home/<vous>/.ansible/collections:/usr/share/ansible/collections
  executable location = /home/<vous>/.local/bin/ansible
  python version = 3.12.x (...) [GCC 13.3.0] (/home/<vous>/.local/share/pipx/venvs/ansible/bin/python)
  jinja version = 3.1.6
  pyyaml version = 6.0.3 (with libyaml v0.2.5)
```

🔍 **Observation** (three lines to analyze):

| Line | What it tells you |
| --- | --- |
| `ansible [core 2.x.y]` | The `ansible-core` version. The RHCE 2026 target expects **`core 2.18+`** (RHEL 9/10). |
| `config file =` | The loaded `ansible.cfg`. Must point to **the repo's one** when you are inside it (`/.../ansible-training/ansible.cfg`). Otherwise, your local settings will not apply. |
| `executable location =` | The binary's **path**. If it is `~/.local/bin/ansible` (a wrapper pointing to `~/.local/share/pipx/venvs/ansible/...`) → pipx install. If `/usr/bin/...` → distro package. If `~/.local/share/mise/shims/...` → mise. This is how you identify the method. |

## 📚 Exercise 2 — Are all 8 standard binaries present?

Ansible is not a single binary: it is a **family of 8 commands** that you will use in turn (lab 03 covers them all). Check that none is missing:

```bash
for bin in ansible ansible-playbook ansible-galaxy ansible-doc \
           ansible-vault ansible-config ansible-inventory ansible-lint; do
  command -v "$bin" || echo "$bin MANQUANT"
done
```

🔍 **Observation**: every binary must return a path. Typical cases:

- **`ansible-lint MANQUANT`**: not shipped by default with `pipx install ansible`. Run `pipx install ansible-lint` or `pipx inject ansible ansible-lint`.
- **`ansible-vault MANQUANT`**: suspicious. `vault` ships with `ansible-core`, so this is the sign of a broken installation. Reinstall Ansible.

## 📚 Exercise 3 — How many modules are available?

```bash
ansible-doc -l | wc -l
```

🔍 **Observation**: you should get **several thousand** (~10,000+). This number is **not** what `ansible-core` alone ships (which contains ~70 modules under `ansible.builtin.*`): it is what `ansible-core` **+ all installed collections** ship.

- **<100 modules**: collections are missing. Run `ansible-galaxy collection install -r requirements.yml` at the repo root.
- **~70 modules exactly**: you are on pure `ansible-core`, without collections. Same fix.

## 📚 Exercise 4 — Are the key collections installed?

The repo depends on 3 collections (declared in `requirements.yml`):

```bash
ansible-galaxy collection list | grep -E "ansible.posix|community.general|community.libvirt"
```

Expected output (excerpt):

```text
ansible.posix              2.1.0
community.general          11.4.7
community.libvirt          2.2.0
```

🔍 **Observation**:

- **`ansible.posix`**: standard POSIX modules (`firewalld`, `mount`, `selinux`, `sysctl`). Essential for the server labs.
- **`community.general`**: very broad, utilities (`timezone`, `archive`, `pacman`, etc.).
- **`community.libvirt`**: used by the repo's provisioning infra (VM creation).

If one is missing:

```bash
cd $ANSIBLE_TRAINING
ansible-galaxy collection install -r requirements.yml
```

## 📚 Exercise 5 — Automated verification

The CLI replays the 4 previous checks and tells you which ones pass:

```bash
dsoxlab check decouvrir-installation-ansible
```

🔍 **Observation**: expected output (excerpt):

```text
===> 1. ansible --version
ansible [core 2.20.1]
  config file = /home/.../ansible-training/ansible.cfg
  ...

===> 2. Binaires Ansible standard
  ✓ ansible
  ✓ ansible-playbook
  ✓ ansible-galaxy
  ...

===> 3. Nombre de modules disponibles
  modules disponibles : 12345

===> 4. Collections clés
ansible.posix              2.1.0
community.general          11.4.7
community.libvirt          2.2.0
```

If a check fails (missing binary, absent collection), fix it **before** moving on to lab 03.

## 🔍 Observations to note

- `ansible-core` ≠ `ansible`: `core` is the engine (`ansible.builtin.*` modules), `ansible` is the metapackage that adds the base collections.
- The `executable location =` from `ansible --version` is the **number one indicator** of your installation method. Memorize it, it is the first thing to look at when there is a problem.
- `ansible.cfg` is searched in this order: **(1)** the `ANSIBLE_CONFIG` env variable, **(2)** `./ansible.cfg`, **(3)** `~/.ansible.cfg`, **(4)** `/etc/ansible/ansible.cfg`. The first found wins, no merge. That is why you must **run Ansible from the repo root**.
- A collection is **versioned** (e.g. `ansible.posix 2.1.0`). Updating Ansible does **not** automatically upgrade the collections: you need `ansible-galaxy collection install --upgrade`.

## 🤔 Reflection questions

1. You work on 3 projects: an RHCE 2026 project that requires `ansible-core 2.18+`, a legacy project that breaks beyond `core 2.14`, and an experimental project on `core 2.20`. Which installation method do you choose, and why?

2. A colleague tells you: "My `ansible --version` shows `core 2.16` but I did run `pipx install ansible` with the most recent command." What is the first hypothesis to check?

3. Why is it important that `config file =` points to the repo's `ansible.cfg`, and not to `~/.ansible.cfg` or `/etc/ansible/ansible.cfg`? Which repo setting would be lost otherwise?

## 🚀 Final challenge

The challenge ([`challenge/README.md`](challenge/README.md)) asks you to write a `solution.sh` script that automates the 4 checks with a **clear exit code** (0 if all is well, 1 otherwise). It is the kind of check you would put in a CI job or as a pre-commit hook.

```bash
pytest -v labs/decouvrir/installation-ansible/challenge/tests/
```

## 💡 Going further

- **Try `mise`**: create a `.tool-versions` in a test folder containing `ansible 2.18.0`, enter the folder, and check that `ansible --version` automatically switches to that version.
- **Try an Execution Environment**: follow the EE section of the blog page to build an EE with `ansible-builder` then run a playbook via `ansible-navigator run playbook.yml --mode stdout`. Compare the result with your local install: it is the reference approach for RHCE 2026 (total reproducibility via an OCI image).
- **Audit the active configuration**: `ansible-config dump --only-changed` shows only the settings that differ from the defaults. Useful to understand what the repo's `ansible.cfg` actually changes.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/decouvrir/installation-ansible/lab.yml

# Lint your challenge solution
ansible-lint labs/decouvrir/installation-ansible/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/decouvrir/installation-ansible/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.

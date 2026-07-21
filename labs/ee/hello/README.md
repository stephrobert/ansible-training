# Lab 84 — Hello Execution Environment

> 💡 **Prerequisites**:
> - **Podman** installed (`podman --version`).
> - **ansible-navigator** installed (`pipx install ansible-navigator`).
> - 4 lab VMs reachable (`ansible all -m ansible.builtin.ping` answers `pong`).

## 🧠 Recap

🔗 [**Introducing Execution Environments**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/presentation/)

An **Execution Environment (EE)** is an **OCI container image** that packages `ansible-core`, `ansible-runner`, Ansible **collections**, **Python dependencies** and **system dependencies**. The EE guarantees that the **same** Ansible **runtime** runs from the laptop to the AAP controller: no more "it works on my machine".

**Ansible Navigator** runs a playbook **inside an EE** instead of running it directly with `ansible-playbook`. Benefits: **isolation**, **reproducibility**, **rich debugging** (TUI or stdout, JSON artifacts, replay).

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Check** that Podman and ansible-navigator are installed.
2. **Pull** an EE image (`quay.io/ansible/creator-ee:latest`).
3. **Configure** `ansible-navigator.yml` with a default EE.
4. **Run** a first playbook inside the EE (`stdout` mode and interactive mode).
5. Compare classic **`ansible-playbook`** vs **`ansible-navigator run`**.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING/labs/ee/hello/

# Check the required tools
./setup-ee.sh
```

## ⚙️ Target tree

```text
labs/ee/hello/
├── README.md
├── setup-ee.sh                     ← checks podman + ansible-navigator
├── inventory.yml                    ← inventory of 3 lab VMs
├── ping.yml                         ← demo playbook (ansible.builtin.ping)
├── ansible-navigator.yml            ← default EE config + stdout mode
└── challenge/
    └── tests/
        └── test_ee_hello.py        ← structural tests (6 tests)
```

## 📚 Exercise 1 — Pulling the EE image

```bash
podman pull quay.io/ansible/creator-ee:latest
podman images | grep creator-ee
```

Typical output:

```text
quay.io/ansible/creator-ee  latest  abc123def  3 days ago  1.2 GB
```

🔍 **Observation**: the image is **~1 GB** because it embeds ansible-core, ansible-runner, ansible-lint, ansible-navigator, and many collections (`ansible.posix`, `community.general`, `community.kubernetes`...). It is the **most complete community EE**, ideal for training and development.

## 📚 Exercise 2 — Running a playbook with ansible-navigator (stdout mode)

```bash
ansible-navigator run ping.yml \
  -i inventory.yml \
  --eei quay.io/ansible/creator-ee:latest \
  -m stdout
```

Expected output:

```text
PLAY [Lab 84 — Premier run avec ansible-navigator + EE] *********

TASK [Ping via le module ansible.builtin.ping] *****
ok: [db1.lab]
ok: [web1.lab]
ok: [web2.lab]

PLAY RECAP *****************************************
db1.lab  : ok=1  changed=0  unreachable=0  failed=0
web1.lab : ok=1  changed=0  unreachable=0  failed=0
web2.lab : ok=1  changed=0  unreachable=0  failed=0
```

🔍 **Observation**: the output looks like classic `ansible-playbook`. The difference: **Ansible runs inside an ephemeral Podman container**. Check with `podman ps -a`: the container is gone, this is intentional (ephemeral).

## 📚 Exercise 3 — Interactive mode (TUI)

```bash
ansible-navigator run ping.yml \
  -i inventory.yml
# (without -m stdout)
```

The TUI opens:

- **Numbered menu**: type `0` to see the plays, `1` to see the tasks, `2` for the hosts.
- **Drill-down**: select a task, see the result host by host, the raw JSON return, the diff.
- **Keyboard navigation**: arrows, `Esc` to go back up, `:q` to quit.

🔍 **Observation**: the TUI is for **rich debugging**: drill-down task, host, JSON result. Ideal in training and local debugging. **Not suited to CI/CD** where `-m stdout` is preferred.

## 📚 Exercise 4 — `ansible-navigator.yml` configuration

The lab's `ansible-navigator.yml` file holds the default configuration:

```yaml
ansible-navigator:
  execution-environment:
    image: quay.io/ansible/creator-ee:latest
    container-engine: podman
  mode: stdout
```

With this file, the command can be simplified:

```bash
ansible-navigator run ping.yml -i inventory.yml
# → uses creator-ee + stdout mode by default
```

🔍 **Observation**: `ansible-navigator.yml` is looked up in **`./ansible-navigator.yml`**, **`~/.ansible-navigator.yml`**, or via **`$ANSIBLE_NAVIGATOR_CONFIG`**. It lets you pin the EE and the mode for an entire project.

## 📚 Exercise 5 — Comparison ansible-playbook vs ansible-navigator

```bash
# Classic (on the local venv)
time ansible-playbook ping.yml -i inventory.yml

# With EE
time ansible-navigator run ping.yml -i inventory.yml -m stdout
```

| Criterion | `ansible-playbook` | `ansible-navigator run` |
|---------|--------------------|-------------------------|
| Startup | Immediate (~0.5 s) | +1-3 s (Podman launch) |
| Reproducibility | Depends on local venv | EE pinned, identical everywhere |
| Collections | Those of the venv | Those of the EE |
| Debug | `-vvv` text | TUI + JSON artifacts |
| CI/CD | Python setup + collections | `podman run` + EE image |

🔍 **Observation**: **navigator** adds ~1-3 s per run (Podman overhead) in exchange for **reproducibility**. For fast dev iteration: `ansible-playbook`. For production, training, CI/CD: `ansible-navigator`.

## 🔍 Observations to note

- **Idempotence**: a second run of your solution must show `changed=0`
  everywhere in the `PLAY RECAP`. This is the mechanical signal of a playbook
  compliant with best practices.
- **Explicit FQCN**: always prefer `ansible.builtin.<module>` (or the
  appropriate collection) over the short name. `ansible-lint --profile
  production` checks it.
- **Targeting convention**: this lab targets your local machine. To adapt it to
  another group, adjust `hosts:` in `lab.yml`/`solution.yml` then rerun.
- **Isolated reset**: `dsoxlab clean <lab-id>` at the lab root cleanly uninstalls
  what the solution set up so you can replay the scenario.

## 🤔 Reflection questions

1. Why is the first run with navigator slower? (Hint: `podman pull`).

2. One developer uses `ansible-playbook` locally, another uses `ansible-navigator` with an EE. **What risk** does this divergence introduce?

3. How do you **force** ansible-navigator to use **Docker** instead of Podman? And why would you do it?

4. What is `volume-mounts` for in `ansible-navigator.yml`? What happens without it for the SSH keys?

## 🚀 Final challenge

The challenge ([`challenge/tests/`](challenge/tests/)) validates the lab structure through 6 pytest tests (setup script, valid inventory, correct ansible-navigator.yml).

```bash
LAB_NO_REPLAY=1 pytest -v challenge/tests/
```

## 💡 Going further

- **Lab 85**: inspect an EE (collections, ansible-core version, Python deps).
- **Lab 86**: build your own EE with `ansible-builder`.
- **Full `ansible-navigator.yml` configuration**: `playbook-artifact.enable`, `logging`, `time-zone`, `lint.config`.
- **Environment variables**: `ANSIBLE_NAVIGATOR_EE_IMAGE`, `ANSIBLE_NAVIGATOR_MODE`.
- **Red Hat AAP EE**: `registry.redhat.io/ansible-automation-platform-25/ee-supported-rhel9` (Subscription).

## 🔍 Security — 2026 best practices

- **Pinned image**: `creator-ee:v25.5.0` rather than `:latest` in production.
- **SSH volume-mounts** in `ro,Z` (read-only + SELinux label).
- **No secret in a container env variable**: pass via `--vault-password-file` or a secret manager.
- **`pull.policy: missing`** in dev (fast), **`always`** in CI (always the latest version).
- **Image signature**: verify with `cosign verify` before pulling in production.

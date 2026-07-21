# Lab 03 — Getting started with the CLI (the 8 everyday commands)

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

🔗 [**Getting started with the Ansible CLI: the 8 everyday commands**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/prise-en-main-cli/)

Ansible is operated through **8 commands** that each have a precise role. Most labs use only 2 of them (`ansible` and `ansible-playbook`), but in production you will regularly touch the other 6 to diagnose, secure or lint your code.

| Command | What it is for | When to use it |
| --- | --- | --- |
| **`ansible`** | Run **a single module** on a host pattern (ad-hoc mode) | Test, troubleshoot, run a one-off operation |
| **`ansible-playbook`** | Run a **YAML playbook** | 90% of the time |
| **`ansible-doc`** | **Offline** documentation of modules | Before using an unknown module |
| **`ansible-config`** | See the **active configuration** | When a behavior surprises you |
| **`ansible-inventory`** | Validate the **inventory** (groups, resolved vars) | Before a deployment, when debugging |
| **`ansible-galaxy`** | Install **collections** and **roles** | Setting up a project, updating |
| **`ansible-vault`** | **Encrypt** sensitive files | Passwords, API keys, certificates |
| **`ansible-lint`** | Detect **anti-patterns** | Before a commit, in CI |

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Run an **ad-hoc** command on all managed nodes.
2. Find a module's doc **without Internet** via `ansible-doc`.
3. Inspect the resolved **active configuration** and **inventory**.
4. List and install **collections** via `ansible-galaxy`.
5. **Encrypt / decrypt** a variables file with `ansible-vault`.
6. **Lint** a playbook with `ansible-lint`.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping
```

Expected response: 4 `pong` (one per managed node). If it fails, run `dsoxlab provision` at the root.

## 📚 Exercise 1 — `ansible`: ad-hoc command

The **ad-hoc** mode runs a single module on a host pattern, without a playbook. Ideal to test a connection or collect a one-off piece of information.

```bash
ansible all -m ansible.builtin.ping
```

🔍 **Observation**: 4 `pong` must come back. The `ping` module is **not** ICMP: it opens an SSH connection then runs a tiny Python script on the managed node. It is therefore an **end-to-end test** of the whole Ansible chain (SSH + remote Python).

Useful variants:

```bash
ansible webservers -m ansible.builtin.command -a "uptime"           # uptime on the web servers
ansible db1.lab -b -m ansible.builtin.dnf -a "name=tree state=absent"    # uninstall a package
ansible all -m ansible.builtin.setup -a "filter=ansible_distribution"    # collect a fact
```

## 📚 Exercise 2 — `ansible-playbook`: run a playbook

```bash
ansible-playbook labs/bootstrap/prepare-managed-nodes/playbook.yml
```

🔍 **Observation**: the preparation playbook runs. On the **first run**, some tasks are marked `changed`. On the **second run**, the `PLAY RECAP` shows `changed=0` everywhere: this is the idempotence of lab 01 in action.

> 💡 All the `ansible-playbook` commands in the repo run **from the root**: that is why the inventory uses a relative path `{{ inventory_dir }}/../ssh/id_ed25519`.

## 📚 Exercise 3 — `ansible-doc`: offline documentation

`ansible-doc` is your **local manual**: no Internet needed to understand a module.

```bash
ansible-doc ansible.builtin.dnf | less
```

🔍 **Observation**: a module's doc has 4 key sections:

- **Description** (at the top): what the module is for.
- **Options**: all the parameters with their **type**, **default**, and `required` flag.
- **Examples**: ready-to-copy YAML snippets.
- **Returns**: the attributes available in `register:` (useful from lab 17 on).

To list all modules of a collection:

```bash
ansible-doc -l ansible.builtin | head -20      # ansible.builtin modules only
ansible-doc -l | grep -i firewall              # filter by keyword
```

## 📚 Exercise 4 — `ansible-config`: active configuration

When Ansible behaves unexpectedly (a long timeout, missing facts, SSH warnings), it is almost always **a config setting** overriding the default.

```bash
ansible-config dump --only-changed
```

🔍 **Observation**: the output lists **only** the settings that differ from the default, with their **source**:

```text
DEFAULT_HOST_LIST(/.../ansible-training/ansible.cfg) = ['/.../inventory/hosts.yml']
HOST_KEY_CHECKING(/.../ansible-training/ansible.cfg) = False
INTERPRETER_PYTHON(/.../ansible-training/ansible.cfg) = auto_silent
```

Each line says **which setting is modified** + **by which file**. If a behavior surprises you, run this command first.

## 📚 Exercise 5 — `ansible-inventory`: validate the inventory

```bash
ansible-inventory --graph
```

🔍 **Observation**: tree view of the groups:

```text
@all:
  |--@control:
  |  |--control-node.lab
  |--@webservers:
  |  |--web1.lab
  |  |--web2.lab
  |--@dbservers:
  |  |--db1.lab
  |--@rhce_lab:
  |  |--@webservers:
  ...
```

To see **all the resolved variables** of a host (useful when debugging `group_vars` inheritance):

```bash
ansible-inventory --host web1.lab
```

## 📚 Exercise 6 — `ansible-galaxy`: manage collections

List what is already installed:

```bash
ansible-galaxy collection list
```

🔍 **Observation**: you should see at least `ansible.posix`, `community.general`, `community.libvirt` (see lab 02). To install a new collection:

```bash
ansible-galaxy collection install community.docker
```

To reinstall all the repo's collections in one command:

```bash
ansible-galaxy collection install -r requirements.yml
```

## 📚 Exercise 7 — `ansible-vault`: encrypt a secret

You will **never** store a plaintext password in a Git repo. `ansible-vault` encrypts a file (or a single variable) with AES-256.

```bash
echo "api_key: secret-ABC123" > /tmp/secrets.yml
ansible-vault encrypt /tmp/secrets.yml         # asks for a password (enter "test")
cat /tmp/secrets.yml                            # → encrypted content ($ANSIBLE_VAULT;1.1;AES256...)
ansible-vault view /tmp/secrets.yml             # → displays in plaintext (password prompted)
ansible-vault decrypt /tmp/secrets.yml          # → back to plaintext on disk
rm /tmp/secrets.yml
```

🔍 **Observation**:

- An encrypted file **always** starts with `$ANSIBLE_VAULT;1.1;AES256` (the `1.1` is the format version).
- `view` does not touch the disk (read-only). `decrypt` rewrites the file in plaintext.
- The password can be passed via **`--vault-password-file`** (for CI/CD) instead of being typed by hand. This is what the challenge does.

## 📚 Exercise 8 — `ansible-lint`: code quality

`ansible-lint` detects the **anti-patterns** in a playbook: task without `name:`, missing FQCN, deprecated modules, `shell:` without `creates:`, etc.

```bash
ansible-lint labs/bootstrap/prepare-managed-nodes/playbook.yml
```

🔍 **Observation**: if the playbook is compliant, **empty output** (and exit 0). Otherwise, each violation is listed with the line number and the broken rule.

The **production** profile (the strictest):

```bash
ansible-lint --profile production labs/bootstrap/prepare-managed-nodes/
```

## 📚 Exercise 9 — Chain it all

Chain the 6 toolbox commands yourself, in this order:

```bash
ansible all -m ansible.builtin.ping
ansible-doc -l | head
ansible-config dump --only-changed
ansible-inventory --graph
ansible-galaxy collection list
ansible-lint --version
```

🔍 **Observation**: the chain `ansible ping → ansible-doc -l → ansible-config dump → ansible-inventory --graph → ansible-galaxy list → ansible-lint`. If **all** the outputs are clean, your machine is ready for the following labs.

## 🔍 Observations to note

- **`ansible`** (no suffix) = ad-hoc. **`ansible-playbook`** = playbook. Do not confuse them.
- The **FQCN** (`ansible.builtin.dnf` instead of `dnf`) is **mandatory** for RHCE 2026 and strongly recommended everywhere: it guarantees that Ansible calls the right module when several collections expose one with the same name.
- `ansible-doc` reads the doc **embedded** in the Python module: so it is available offline and always up to date with your installed version.
- `ansible-vault` encrypts **a whole file**. To encrypt **a single variable** in a plaintext YAML file, use `ansible-vault encrypt_string` (seen later, Vault section).
- `ansible-lint --profile production` is the strict mode. There are also `min`, `basic`, `moderate`, `safety`, `shared` from least to most strict.

## 🤔 Reflection questions

1. You want to **quickly** check that the 4 managed nodes are reachable and that sudo works. Which command do you use? With `ansible -b`? `-m ping`? `-m command -a "id"`?

2. A colleague tells you: "My playbook takes 30 seconds to start whereas it used to be instant." Which command do you run first to diagnose?

3. You want to encrypt **a single password** in a `vars.yml` file that already contains 10 other non-sensitive variables. Is `ansible-vault encrypt` the right tool? If not, which one?

## 🚀 Final challenge

The challenge ([`challenge/README.md`](challenge/README.md)) asks you to write a `solution.sh` script that automates a full `ansible-vault` cycle (encrypt → check the header → decrypt) with a password file (`--vault-password-file`). This is the pattern used in CI when the password is provided by a secret manager.

```bash
pytest -v labs/decouvrir/prise-en-main-cli/challenge/tests/
```

## 💡 Going further

- **`ansible-navigator`**: a TUI wrapper that runs playbooks inside an Execution Environment (OCI image), recommended for RHCE 2026. Run `ansible-navigator run labs/bootstrap/prepare-managed-nodes/playbook.yml --mode stdout` to see the difference.
- **`ansible-builder`**: builds custom Execution Environments from a YAML file. This is how you guarantee that a playbook runs **identically** on the dev machine, in CI and in production.
- **Git pre-commit hooks**: integrate `ansible-lint --profile production` into a pre-commit hook to block commits that would introduce anti-patterns.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/decouvrir/prise-en-main-cli/lab.yml

# Lint your challenge solution
ansible-lint labs/decouvrir/prise-en-main-cli/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/decouvrir/prise-en-main-cli/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.

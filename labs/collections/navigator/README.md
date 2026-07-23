# Lab — Automation content navigator (`ansible-navigator`)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → "pong" expected
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root.

## 🧠 Recap

🔗 [**Automation content navigator**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/ansible-navigator/)

`ansible-navigator` is the **Automation content navigator**: the modern front-end
that Red Hat pushes to replace the scattered `ansible-*` commands. One tool for
`run`, `doc`, `collections`, `inventory`, `config`, `images`, either in a TUI or in
`--mode stdout` for scripts and CI. It is an **exam objective** of the RHCE EX294:

- *Use Automation content navigator to find new modules in available Ansible
  Content Collections and use them.*
- *Use Automation content navigator to create inventories and configure the
  Ansible environment.*

By default `ansible-navigator` runs everything **inside an Execution Environment**
(a container). In this lab we pass `--execution-environment false` so it uses the
local ansible install directly: the skill (subcommands and workflow) is identical,
without pulling a multi-hundred-MB image.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Discover** a module inside an installed collection with
   `ansible-navigator doc <fqcn>` and `ansible-navigator collections`.
2. **Use** that discovered module in a playbook to produce a real, verifiable
   system state.
3. **Validate** an inventory with `ansible-navigator inventory --list`.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible-navigator --version
ansible all -m ansible.builtin.ping
```

## 📚 Exercise 1 — List collections and modules with the navigator

```bash
# Browse every installed collection
ansible-navigator collections --mode stdout --execution-environment false

# Read a module's documentation without leaving the navigator
ansible-navigator doc ansible.posix.sysctl --mode stdout --execution-environment false
```

🔍 **Observation**: `ansible-navigator doc <FQCN>` is the navigator equivalent of
`ansible-doc`. It shows the doc of the **installed** version and confirms which
collection ships the module (here `ansible.posix`). That is exactly how you *find a
new module in a collection*.

## 📚 Exercise 2 — Use the discovered module

Once you know `ansible.posix.sysctl` exists and what it expects, call it from a
play to set a kernel parameter. The point of the navigator is not to read docs, it
is to go from *"which module do I need?"* to *"the system is in the right state"*.

```yaml
- name: Apply the discovered module
  ansible.posix.sysctl:
    name: vm.swappiness
    value: "42"
    sysctl_set: true
    state: present
    reload: true
    sysctl_file: /etc/sysctl.d/70-navigator-lab.conf
```

🔍 **Observation**: `sysctl_set: true` changes the **live** value, `sysctl_file`
persists it. The module is idempotent: a second run reports no change.

## 📚 Exercise 3 — Validate an inventory with the navigator

```bash
ansible-navigator inventory -i my-inventory.yml --list \
  --mode stdout --execution-environment false
```

🔍 **Observation**: `ansible-navigator inventory` resolves and renders an
inventory just like `ansible-inventory`. Use it to **prove** that a hand-written
inventory parses, that groups and `ansible_host` are correct, before a single play
runs against it.

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md): use `ansible-navigator` to
discover a module, drop a **proof** of that exploration, use the module to set a
kernel state on `db1.lab`, and validate an inventory with
`ansible-navigator inventory`.

## 💡 Going further

- `ansible-navigator run playbook.yml` replays a playbook inside an EE and keeps a
  browsable **artifact** of the run.
- `ansible-navigator config` and `ansible-navigator settings` inspect the resolved
  Ansible / navigator configuration.
- Set a project `ansible-navigator.yml` to pin the default EE, the pull policy and
  the mode for the whole team.

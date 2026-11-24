# The playbook that only your laptop can run

## The situation

The release failed at 2am and the on-call engineer could not take over. The
playbook runs on your machine and only yours: you have a collection installed
that nobody else does, a Python library pinned by accident three months ago, and
an `ansible-core` version that no longer matches the one on the CI runner. Every
handover ends the same way, with a wiki page listing what to install and a
colleague halfway through it. The runtime has to travel with the playbook.

Your mission, from the project directory:

1. Pull an official **Execution Environment** image with Podman, so the entire
   Ansible runtime becomes one versioned artefact instead of a wiki page.
2. Declare it as the **default environment** for the project, and script the
   prerequisites check so a newcomer gets a working setup without asking anyone.
3. Run a playbook **inside** the EE against **web1.lab** and **db1.lab**, proving
   the container reaches the managed nodes as well as a local run would.
4. Compare the two runs, plain and containerised, and name what actually changed:
   what is now guaranteed, and what it costs you.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/presentation/ (in French)

## 🎯 Challenge — Run a first playbook inside an EE

### ✅ Objective

At the lab root, produce 4 files that demonstrate the use of
`ansible-navigator` with an official Execution Environment
(`community-ansible-dev-tools`).

| File | Expectation |
| --- | --- |
| `setup-ee.sh` | Executable. Checks/installs `podman` and `ansible-navigator`. |
| `inventory.yml` | Valid YAML. Hosts `web1.lab` and `db1.lab` in the `all` group, each declaring its `ansible_host` (reachable IP). |
| `ping.yml` | FQCN module `ansible.builtin.ping`. |
| `ansible-navigator.yml` | References the `community-ansible-dev-tools` image in `execution-environment.image:`. |

### 🧩 Stuck?

```bash
dsoxlab hint ee-hello
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

```bash
cd labs/ee/hello/
./setup-ee.sh
ansible-navigator run ping.yml -i inventory.yml --mode stdout
```

### 📓 Command log

Record in `challenge/solution.sh` the commands you ran (setup,
navigator run). This log must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/ee/hello/challenge/tests/
```

The tests actually run `bash -n` on your script,
`ansible-inventory` on your inventory and `ansible-playbook
--syntax-check` on your playbook. Only the run inside the EE (Podman + pull
of community-ansible-dev-tools) stays manual.

### 🧹 Reset

```bash
dsoxlab clean ee-hello
```

### 💡 Going further

- `ansible-navigator --mode interactive`: keyboard-navigable TUI interface
  (`:run`, `:doc`, `:collections`).
- `--pp always`: forces a pull on every run (useful in CI when
  you push the EE often).
- `~/.ansible-navigator.yml`: global config instead of per-project.

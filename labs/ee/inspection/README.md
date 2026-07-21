# Lab 85 — Inspecting Execution Environments

> 💡 **Prerequisite**: having completed [lab 84](../hello/) (Podman + ansible-navigator installed).

## 🧠 Recap

🔗 [**Inspect an EE: images, doc, collections**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/lookup-doc/)

Before **building your own EE** (lab 86), you must know how to **inspect** an existing EE: which embedded collections? which ansible-core version? which Python dependencies? which system packages? Ansible Navigator provides **`ansible-navigator images`** for this TUI exploration, and **`ansible-navigator doc`** for the doc of a given module from the EE.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **List** the collections of an EE (`ansible-navigator images` or `podman run ... ansible-galaxy`).
2. **Compare** 3 community EEs: `creator-ee`, `awx-ee`, `community-ee-minimal`.
3. **Read the doc** of a module in the context of the EE (`ansible-navigator doc`).
4. **Choose** the EE suited to a use case: training, AWX, minimalist production.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING/labs/ee/inspection/
./inspect.sh
```

## ⚙️ Tree

```text
labs/ee/inspection/
├── README.md
├── inspect.sh                       ← compares 3 EEs and lists collections
└── challenge/
    └── tests/
        └── test_ee_inspection.py    ← structural tests (4 tests)
```

## 📚 Exercise 1 — TUI inspection with ansible-navigator images

```bash
ansible-navigator images --eei quay.io/ansible/creator-ee:latest
```

The TUI opens with **5 sections** numbered:

```text
0 │ Image information     ← ID, size, registry
1 │ Image layers          ← Dockerfile layers
2 │ OS release            ← UBI 9 / RHEL 9 / Fedora
3 │ System packages       ← rpm -qa
4 │ Ansible version       ← ansible-core
5 │ Ansible collections   ← ansible-galaxy collection list
6 │ Python packages       ← pip list
7 │ Python version        ← python3 --version
```

Navigate into `5` (collections): there you find `ansible.posix`, `community.general`, `ansible.utils`, `community.kubernetes`, etc., **with their exact versions**.

🔍 **Observation**: this is **the** command to answer "before building my EE, what is already in `creator-ee`?". It avoids reinstalling collections that are already present.

## 📚 Exercise 2 — Compare 3 community EEs

| EE | Size | Use case |
|----|--------|-------------|
| **`quay.io/ansible/creator-ee`** | ~1.2 GB | Training, dev. Rich: ansible-lint, navigator deps, many collections. |
| **`quay.io/ansible/awx-ee`** | ~900 MB | AWX upstream. AWX collections by default. |
| **`ghcr.io/ansible-community/community-ee-minimal`** | ~400 MB | **Minimal** base: starting point for a custom EE. |

Run the script:

```bash
./inspect.sh
```

The script pulls the 3 EEs, displays the sizes, lists the collections of creator-ee, and compares the ansible-core versions.

🔍 **Observation**: for **a custom production EE**, starting from **`community-ee-minimal`** and adding **only** the necessary collections is the strategy that produces the smallest and least exposed image.

## 📚 Exercise 3 — Read the doc of a module in the EE

```bash
ansible-navigator doc ansible.builtin.copy --eei quay.io/ansible/creator-ee:latest
```

The TUI displays:

- **Synopsis** of the module.
- **Parameters** with types, default values, examples.
- **Examples** YAML directly copyable.
- **Return values**: what the module returns in `register:`.

🔍 **Observation**: the doc displayed is **that of the version embedded in the EE**, not the internet doc. It guarantees that the mentioned parameters are indeed available with the Ansible version used.

## 📚 Exercise 4 — List the embedded collections (CLI mode)

```bash
ansible-navigator collections --eei quay.io/ansible/creator-ee:latest
```

Output:

```text
0 │ ansible.builtin           2.18.1
1 │ ansible.posix             2.0.0
2 │ community.general         10.5.0
3 │ kubernetes.core            5.1.1
…
```

For a scriptable format:

```bash
podman run --rm quay.io/ansible/creator-ee:latest \
  ansible-galaxy collection list --format json | jq
```

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

1. For an Ansible training **with K8s**, which EE do you take? Why?

2. For a **minimalist** production deploying **only** Linux servers, which EE?

3. How do you **verify** that an EE contains a specific collection and its version, **without** pulling it locally?

4. Why is `creator-ee` the largest? What can you remove to make your own lighter EE?

## 🚀 Final challenge

The challenge ([`challenge/tests/`](challenge/tests/)) validates that the inspection script indeed references the 3 EEs and uses the reference commands.

```bash
LAB_NO_REPLAY=1 pytest -v challenge/tests/
```

## 💡 Going further

- **`ansible-navigator config`**: see the Ansible config **inside** the EE (different from the local config).
- **`skopeo inspect docker://quay.io/...`**: inspect without pulling (saves bandwidth).
- **`crane manifest`**: alternative to skopeo, faster.
- **Lab 86**: create your own custom EE.
- **Red Hat AAP EE**: `ee-supported-rhel9` contains the **Red Hat certified** collections.

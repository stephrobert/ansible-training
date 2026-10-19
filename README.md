# Ansible Training: RHCE EX294

**Language:** [English](./README.md) · [Français](./README.fr.md)

[![CI](https://github.com/stephrobert/ansible-training/actions/workflows/ci.yml/badge.svg)](https://github.com/stephrobert/ansible-training/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/stephrobert/ansible-training?label=OpenSSF%20Scorecard)](https://securityscorecards.dev/viewer/?uri=github.com/stephrobert/ansible-training)
[![Plumber compliance](https://score.getplumber.io/github.com/stephrobert/ansible-training.svg)](https://score.getplumber.io/github.com/stephrobert/ansible-training)
[![SLSA 3](https://slsa.dev/images/gh-badge-level3.svg)](https://slsa.dev)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](./LICENSE)

Hands-on **Ansible** training, driven by the
[`dsoxlab`](https://github.com/stephrobert/dsoxlab) CLI. This repository is the
**lab catalog** for the Ansible track of
[www.stephane-robert.info](https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/),
aimed at the **RHCE (EX294)** certification, with idempotency as its common
thread.

## What this is

`ansible-training` is a **content repository**, not an application. It provides:

- **guided labs**, with precise instructions,
- **challenges** with no walkthrough, to check you can work on your own,
- an **EX294 mock exam** that pulls everything together,
- **automated validation** that proves the state of the managed nodes (rather
  than that a playbook was written),
- **scoring** with cost-weighted hints.

The `dsoxlab` CLI is the single entry point: it prepares a lab, shows the
mission, validates, scores and reports. It lives in **its own repository** and
is installed **separately**: it is not part of this repo.

## Requirements

- Python 3.11+ and [`uv`](https://docs.astral.sh/uv/)
- [`mise`](https://mise.jdx.dev/) for the Ansible toolchain (see below)
- `git`
- **KVM/libvirt**: the labs need 4 AlmaLinux 9 VMs (1 control node, 3 managed
  nodes). Budget around 6 GB of RAM and 55 GB of disk.

## Installation

```bash
# 1. The dsoxlab CLI (external tool, stays out of this repo)
uv tool install dsoxlab        # or: pipx install dsoxlab

# 2. This lab catalog
git clone https://github.com/stephrobert/ansible-training.git
cd ansible-training

# 3. The Ansible toolchain, at exam versions
mise install                   # ansible-core 2.18, ansible-lint, molecule, yamllint

# 4. The 4 VMs, prepared (~5 min)
mise run provision

# 5. Browse and play
dsoxlab list-labs
dsoxlab run <lab-id>
dsoxlab check <lab-id>
```

### Your first lab

**Start with the `decouvrir` section.** `bootstrap` prepares the
infrastructure; it is not the pedagogical entry point.

```bash
dsoxlab use decouvrir                 # starting section
dsoxlab next                          # → decouvrir-declaratif-vs-imperatif
```

Then, for this lab and every other one, the same four-step cycle:

```bash
dsoxlab course <id>        # 1. the context, then the course
dsoxlab challenge <id>     # 2. what is asked of you
dsoxlab run <id>           # 3. prepares your workspace and puts you in it
dsoxlab check <id>         # 4. validate and score
```

`run` is the step people skip: it creates the files you work on, and for a `vm`
lab it puts the managed nodes into the state the scenario describes. A `check`
run without `run` fails by reporting that nothing is done — true, but
misleading.

**The 25 `shell` labs need no virtual machine at all**: writing YAML, a Jinja2
template, an inventory, running Molecule or `ansible-lint` all happen on your
own box. You can start without provisioning anything, and only bring the 4 VMs
up when you reach the `vm` labs.

> ⚠️ **`mise run provision`, not `dsoxlab provision` on its own.** The CLI brings
> the VMs up, but it delivers them **bare**: cloud-init sets the account and the
> key, nothing more. The labs, however, target equipped managed nodes
> (`firewalld`, `python3-firewall`, `chrony`). Without that preparation, any lab
> touching the firewall fails with "Failed to import the required Python library
> (firewall)". The `mise` task chains provisioning and bootstrap.
>
> To replay the preparation alone: `mise run bootstrap-nodes`.

`dsoxlab doctor` checks your environment (Python, pytest, runtimes, detected
labs). `mise run setup-hosts` and `mise run setup-ssh` make the lab names
resolvable and configure SSH to use the repository key.

**Why `mise` on top of `dsoxlab`**: the `ansible-core` version is part of the
exercise. A playbook that passes on 2.18 may fail on 2.19, and the EX294 is sat
on a specific version. `mise` pins it, along with the matching lint toolchain.
`dsoxlab` only drives the labs.

### Staying up to date

Labs land in this repository, the CLI evolves on its own. Update each
separately:

```bash
git pull                       # new labs
uv tool upgrade dsoxlab        # the CLI (or: pipx upgrade dsoxlab)
mise install                   # the Ansible toolchain if versions moved
```

Your work in progress lives in each lab's `challenge/` and is not versioned:
`git pull` brings in new labs without ever touching it.

## How it works

### The declarative contract (two levels)

The catalog is described by data, not code: the `dsoxlab` engine stays
domain-agnostic and reads two levels of files.

- **`meta.yml`** at the root declares the repository identity, the
  infrastructure topology (network, hosts, provider) and the **order** of the
  sections shown by `list-labs`.
- **`lab.yaml`** per lab (under `labs/<section>/<lab>/`) declares its `skills`,
  its `level`, its `runtime` (`vm` or `shell`, with the hosts it targets), its
  `distros`, its `doc_url` and a `validation` block. An optional `lab.fr.yaml`
  overrides `title` and `description` in French.

`dsoxlab validate-structure` checks the contract of the labs it **discovered**:
required files present, complete metadata, consistent targets. Careful though,
it does not report a lab declared in `meta.yml` but missing from disk:
discovery is a glob over `labs/**/lab.yaml`, and an invalid `lab.yaml`
disappears from the catalog **silently**. Hence the rule: `dsoxlab list-labs`
first, `validate-structure` second.

### The life cycle of a lab

The learner drives everything from the CLI:

```bash
dsoxlab doctor                        # check the environment
dsoxlab list-labs                     # browse the catalog
dsoxlab show <id>                     # metadata and status of a lab
dsoxlab run <id>                      # prepare and start the environment
dsoxlab challenge <id>                # read the mission (no walkthrough)
dsoxlab hint <id>                     # reveal a hint (deducted from the score)
dsoxlab check <id>                    # run the tests, compute and score
dsoxlab submit <id>                   # final submission, closes the session
dsoxlab progress                      # progress per section, average score
```

`run` is when the environment comes up. For a **shell** lab, the CLI creates the
`workdir` and copies the declared fixtures. For a **vm** lab, it plays the lab's
`setup.yaml` on the managed nodes and opens access to the control node, where
you write your playbooks.

### Topology

A dedicated `lab-ansible` libvirt network (10.10.20.0/24), so it coexists with
the other labs without subnet collisions.

| Host | Role | RAM | vCPU |
| --- | --- | --- | --- |
| `control-node.lab` | control node: where you write your playbooks | 2048 | 2 |
| `web1.lab` | managed node | 1024 | 1 |
| `web2.lab` | managed node | 1024 | 1 |
| `db1.lab` | managed node | 1536 | 1 |

IPs are not declared: Terraform assigns them and the inventory reads them. At
run time `dsoxlab` injects the groups that lab playbooks target: `lab_target`
(the control node), `lab_<role>` (one per managed node in use) and `labenv`
(all of them). A lab never hardcodes a FQDN.

### The accounts: `ansible` (service) and `student` (human)

cloud-init sets up **two accounts** on every node, both hardened the same way:
**SSH key only** (`ssh_pwauth: false`), **no login password**, and
`sudo NOPASSWD:ALL`.

- **`ansible`** is the **service** account through which all automation
  connects, `dsoxlab` as well as the lab playbooks. It is the inventory's
  `ansible_user` and the user in the generated `ssh_config`. Connecting through
  a dedicated service account, separate from the human one, is the **good
  practice**: automation actions are attributable and the account can be revoked
  independently. Its `NOPASSWD:ALL` is deliberate: RHCE automation touches
  everything (dnf, systemd, LVM, SELinux, firewalld); security rests on the
  account being **dedicated**, not on a crippled `sudo` that would break
  automation.
- **`student`** is the **human** account, the one you run `dsoxlab` and
  `ansible` from on the control node. It also exists on the managed nodes for
  debugging, but it is **never** the one driving automation.

Practical consequence: when a lab restricts SSH access (`AllowUsers`) or sets a
`remote_user`, it targets **`ansible`**; restricting it to any other account
would cut automation off. To inspect a node by hand, `dsoxlab ssh <host>`
connects you as `ansible`.

### Runtimes

| Runtime | What it brings |
| --- | --- |
| `vm` | Terraform + libvirt. Real managed nodes: services, packages, users, storage, and **persistence across reboot**. 88 labs. |
| `shell` | What stays local to your box: writing YAML, a Jinja2 template, an inventory, running Molecule or ansible-lint. 25 labs. |

VMs are provisioned once with `dsoxlab provision` and torn down with
`dsoxlab destroy`.

### The validation model

Validation **proves the state of the system, it does not take your word for
it**. Every lab ships `pytest` / `pytest-testinfra` tests under
`challenge/tests/` that check facts on the machine: the service runs **and** is
enabled, the deployed file has the right content **and** the right owner. A test
that merely checks a command was typed is rejected.

Second requirement, specific to Ansible: **idempotency**. A lab whose solution
still reports `changed` when replayed is a broken lab. That is the trap RHCE
candidates fall into, so the tests prove it whenever the subject warrants it.

- In instructor mode, a fixture in the root `conftest.py` **replays the
  reference solution** before the tests, to prove the solution itself is
  correct.
- In `dsoxlab check` (the learner's path), that replay is **disabled**
  (`LAB_NO_REPLAY=1`): the tests validate their own work.

### Scoring, hints, progress

`check` records a score (tests passed out of total, minus the cost of any hints
used). Hints are **cost-weighted**: revealing one removes points, which is why
they are opt-in. History lives in a SQLite database local to the repository
(`.dsoxlab.db`, not versioned); `dsoxlab scores` and `dsoxlab progress` read it.

### Solutions stay encrypted

Reference solutions live in `solution/`, **encrypted with `ansible-vault`**. A
plain-text solution spoils the lab for everyone, and git history keeps it even
after deletion. A `pre-commit` hook checks the encryption header on every commit
rather than taking it on trust.

```bash
mise run solutions-status      # check everything is encrypted
mise run solve <section>/<lab> # apply the official solution (instructor)
```

## Catalog

Labs live under `labs/` and are ordered by `meta.yml`. The list below is
generated: run `python3 scripts/render-readme.py` to refresh it.

<!-- LABS_LIST_START -->

**113 labs** across **23 sections** (source of truth: [`meta.yml`](./meta.yml)).

### Bootstrap

System preparation of the managed nodes, played by `dsoxlab provision`.

- [`bootstrap-prepare-managed-nodes`](./labs/bootstrap/prepare-managed-nodes/): Prepare Ansible managed nodes

### Discover Ansible

First contact: declarative versus imperative, installation, the CLI, configuration.

- [`decouvrir-declaratif-vs-imperatif`](./labs/decouvrir/declaratif-vs-imperatif/): Declarative vs imperative: why Ansible does not drift
- [`decouvrir-installation-ansible`](./labs/decouvrir/installation-ansible/): Ansible installation: verify your control node
- [`decouvrir-configuration-ansible`](./labs/decouvrir/configuration-ansible/): ansible.cfg: precedence and critical options
- [`decouvrir-prise-en-main-cli`](./labs/decouvrir/prise-en-main-cli/): Ansible CLI: the 8 everyday commands

### First steps

A first playbook, and first vault secrets.

- [`premiers-pas-premier-playbook`](./labs/premiers-pas/premier-playbook/): First playbook: install nginx on the webservers
- [`premiers-pas-ansible-vault`](./labs/premiers-pas/ansible-vault/): First steps with ansible-vault

### Write Ansible code

The anatomy of a play, execution control, variables, Jinja2, conditionals, loops, error handling.

- [`ecrire-code-plays-et-tasks`](./labs/ecrire-code/plays-et-tasks/): Plays and tasks: anatomy and execution order
- [`ecrire-code-handlers`](./labs/ecrire-code/handlers/): handlers: the restart-on-config-change pattern
- [`ecrire-code-tags`](./labs/ecrire-code/tags/): tags: target or skip a subset of tasks
- [`ecrire-code-checkmode-diff`](./labs/ecrire-code/checkmode-diff/): check mode and diff: dry-run and change preview
- [`ecrire-code-variables-base`](./labs/ecrire-code/variables-base/): Variables: declaration and scope
- [`ecrire-code-types-collections`](./labs/ecrire-code/types-collections/): Collection types: lists, dicts, nested structures
- [`ecrire-code-facts-magic-vars`](./labs/ecrire-code/facts-magic-vars/): facts and magic vars: ansible_facts, hostvars
- [`ecrire-code-custom-facts`](./labs/ecrire-code/custom-facts/): Custom facts: facts.d and ansible_local
- [`ecrire-code-precedence-variables`](./labs/ecrire-code/precedence-variables/): Variable precedence: the 22 levels
- [`ecrire-code-register-set-fact`](./labs/ecrire-code/register-set-fact/): register and set_fact: capture and create variables
- [`ecrire-code-parallelisme-strategies`](./labs/ecrire-code/parallelisme-strategies/): Parallelism: forks, serial, throttle, strategy
- [`ecrire-code-async-poll`](./labs/ecrire-code/async-poll/): async and poll: long tasks without blocking SSH
- [`ecrire-code-delegation`](./labs/ecrire-code/delegation/): Delegation: delegate_to, run_once, local_action
- [`ecrire-code-lookups`](./labs/ecrire-code/lookups/): lookups: fetch external data at runtime
- [`ecrire-code-jinja2-base`](./labs/ecrire-code/jinja2-base/): Jinja2: interpolation, logic and whitespace
- [`ecrire-code-filtres-jinja-essentiels`](./labs/ecrire-code/filtres-jinja-essentiels/): Essential Jinja2 filters: default, combine, selectattr
- [`ecrire-code-conditions-when`](./labs/ecrire-code/conditions-when/): when conditions: operators and Jinja tests
- [`ecrire-code-boucles-loop`](./labs/ecrire-code/boucles-loop/): loop: iterate over lists and dicts
- [`ecrire-code-boucles-with-deprecated`](./labs/ecrire-code/boucles-with-deprecated/): Legacy with_* loops: migrating to loop
- [`ecrire-code-block-rescue-always`](./labs/ecrire-code/block-rescue-always/): block, rescue, always: try/catch/finally
- [`ecrire-code-failed-when-changed-when`](./labs/ecrire-code/failed-when-changed-when/): failed_when and changed_when: redefine success and change
- [`ecrire-code-ignore-errors`](./labs/ecrire-code/ignore-errors/): ignore_errors: legitimate use vs anti-pattern
- [`ecrire-code-any-errors-fatal`](./labs/ecrire-code/any-errors-fatal/): any_errors_fatal: stop the play on the first error
- [`ecrire-code-filtres-jinja-avances`](./labs/ecrire-code/filtres-jinja-avances/): Advanced Jinja2 filters: regex, b64, password_hash
- [`ecrire-code-tests-jinja`](./labs/ecrire-code/tests-jinja/): Jinja2 tests: is defined, is mapping, is sequence
- [`ecrire-code-module-template`](./labs/ecrire-code/module-template/): template module: validate, backup, whitespace
- [`ecrire-code-lineinfile-vs-template`](./labs/ecrire-code/lineinfile-vs-template/): lineinfile vs template: which module when
- [`ecrire-code-import-include`](./labs/ecrire-code/import-include/): import vs include: static or dynamic

### File modules

Handling files: copy, file, blockinfile, lineinfile, replace, fetch, archive.

- [`modules-fichiers-copy`](./labs/modules-fichiers/copy/): copy module: transfer files and inline content
- [`modules-fichiers-file`](./labs/modules-fichiers/file/): file module: states, permissions and symlinks
- [`modules-fichiers-blockinfile`](./labs/modules-fichiers/blockinfile/): blockinfile module: idempotent multi-line block
- [`modules-fichiers-lineinfile`](./labs/modules-fichiers/lineinfile/): lineinfile module: edit a line in an existing file
- [`modules-fichiers-replace`](./labs/modules-fichiers/replace/): replace module: substitute a pattern in a file
- [`modules-fichiers-fetch`](./labs/modules-fichiers/fetch/): fetch module: retrieve files from managed nodes
- [`modules-fichiers-archive-unarchive`](./labs/modules-fichiers/archive-unarchive/): archive and unarchive modules: compress and extract

### Package modules

Distribution-agnostic package management (package), dnf options, RPM repositories.

- [`modules-paquets-package`](./labs/modules-paquets/package/): package module: distro-agnostic installation
- [`modules-paquets-dnf-options`](./labs/modules-paquets/dnf-options/): dnf module: enablerepo, security, exclude, autoremove
- [`modules-paquets-yum-repository`](./labs/modules-paquets/yum-repository/): yum_repository module: declare an RPM repository

### Service modules

Managing systemd services and cron jobs.

- [`modules-services-systemd`](./labs/modules-services/systemd/): systemd_service module: manage systemd services
- [`modules-services-cron`](./labs/modules-services/cron/): cron module: schedule idempotent jobs

### User modules

Managing users, groups, SSH keys and sudoers.

- [`modules-utilisateurs-user`](./labs/modules-utilisateurs/user/): user module: create, modify and remove accounts
- [`modules-utilisateurs-group`](./labs/modules-utilisateurs/group/): group module: manage Linux groups
- [`modules-utilisateurs-authorized-key`](./labs/modules-utilisateurs/authorized-key/): authorized_key module: user SSH keys
- [`modules-utilisateurs-sudoers`](./labs/modules-utilisateurs/sudoers/): sudoers module: manage sudo rights safely

### RHEL modules

RHEL specifics: firewalld, SELinux, sysctl, mount, parted, filesystem, LVM.

- [`modules-rhel-firewalld`](./labs/modules-rhel/firewalld/): firewalld module: manage the RHEL firewall
- [`modules-rhel-sysctl`](./labs/modules-rhel/sysctl/): sysctl module: persisted kernel parameters
- [`modules-rhel-selinux`](./labs/modules-rhel/selinux/): selinux module: modes, booleans and contexts
- [`modules-rhel-mount`](./labs/modules-rhel/mount/): mount module: manage fstab and mount points
- [`modules-rhel-parted`](./labs/modules-rhel/parted/): parted module: create a disk partition
- [`modules-rhel-filesystem`](./labs/modules-rhel/filesystem/): filesystem module: create a filesystem
- [`modules-rhel-lvm-storage`](./labs/modules-rhel/lvm-storage/): LVM: chaining lvg, lvol, filesystem and mount

### Network modules

Downloads and HTTP calls: get_url, uri.

- [`modules-reseau-get-url`](./labs/modules-reseau/get-url/): get_url module: download a file over HTTP/HTTPS
- [`modules-reseau-uri`](./labs/modules-reseau/uri/): uri module: REST API calls

### Diagnostic modules

Inspection and synchronisation: stat, find, assert/fail, wait_for/pause.

- [`modules-diagnostic-stat`](./labs/modules-diagnostic/stat/): stat module: inspect files and directories
- [`modules-diagnostic-find`](./labs/modules-diagnostic/find/): find module: multi-file search
- [`modules-diagnostic-assert-fail`](./labs/modules-diagnostic/assert-fail/): assert and fail modules: defensive validation
- [`modules-diagnostic-wait-for-pause`](./labs/modules-diagnostic/wait-for-pause/): wait_for and pause modules: synchronization

### Inventories

group_vars and host_vars, host patterns, the dynamic libvirt inventory.

- [`inventaires-statiques`](./labs/inventaires/statiques/): Write a static inventory from scratch: groups, children and group vars
- [`inventaires-group-vars-host-vars`](./labs/inventaires/group-vars-host-vars/): group_vars and host_vars: structured inventory variables
- [`inventaires-patterns-hotes`](./labs/inventaires/patterns-hotes/): Host patterns: wildcards and the :, & and ! operators
- [`inventaires-dynamique-kvm`](./labs/inventaires/dynamique-kvm/): Dynamic KVM inventory with community.libvirt

### Roles

The anatomy of a role, variables, handlers, argument_specs, consuming a role, dependencies, RHEL system roles.

- [`roles-creer-premier-role`](./labs/roles/creer-premier-role/): Create your first role with ansible-galaxy role init
- [`roles-variables-defaults-vars`](./labs/roles/variables-defaults-vars/): Role variables: defaults/ vs vars/ and precedence
- [`roles-handlers-meta`](./labs/roles/handlers-meta/): Role handlers and meta: notify and galaxy_info
- [`roles-argument-specs`](./labs/roles/argument-specs/): argument_specs: validate a role's input variables
- [`roles-consommer-role`](./labs/roles/consommer-role/): Consume a role: roles:, import_role, include_role
- [`roles-dependencies`](./labs/roles/dependencies/): Role dependencies via meta/main.yml
- [`roles-system-roles`](./labs/roles/system-roles/): RHEL system roles: converge time synchronisation with timesync

### Molecule tests

The TDD cycle with Molecule, multi-distribution scenarios.

- [`molecule-introduction`](./labs/molecule/introduction/): Molecule: anatomy of a test scenario
- [`molecule-installation-config`](./labs/molecule/installation-config/): Molecule: enrich a scenario beyond the defaults
- [`molecule-tdd-cycle`](./labs/molecule/tdd-cycle/): Molecule: build a users role test-first
- [`molecule-scenarios-multi-distro`](./labs/molecule/scenarios-multi-distro/): Molecule: test a role across distributions

### Python tests and lint

testinfra, tox across versions, ansible-lint on the production profile.

- [`tests-testinfra`](./labs/tests/testinfra/): Molecule + testinfra: Python assertions on a role
- [`tests-tox-multiversion`](./labs/tests/tox-multiversion/): tox: test a role against several ansible-core versions
- [`tests-ansible-lint-production`](./labs/tests/ansible-lint-production/): ansible-lint production profile with pre-commit

### CI/CD

GitHub Actions and GitLab CI pipelines for roles and collections.

- [`ci-github-actions`](./labs/ci/github-actions/): GitHub Actions: CI workflow for a role
- [`ci-gitlab`](./labs/ci/gitlab/): GitLab CI: parallel:matrix pipeline for a role

### Galaxy and publishing

The ansible-galaxy CLI, requirements.yml, auditing third-party roles, versioning and publishing.

- [`galaxy-ansible-galaxy-cli`](./labs/galaxy/ansible-galaxy-cli/): ansible-galaxy CLI: init, install, list, build, publish
- [`galaxy-installer-roles`](./labs/galaxy/installer-roles/): Install roles and collections from Galaxy or Git
- [`galaxy-auditer-role-existant`](./labs/galaxy/auditer-role-existant/): Audit a Galaxy role before adopting it
- [`galaxy-versionner-publier`](./labs/galaxy/versionner-publier/): Version and publish a role: semver, Git tags, Galaxy

### Ansible Vault

Vault in full: encrypt_string, multiple vault-ids, mixed files, vault inside roles, integration with HashiCorp and Passbolt.

- [`vault-introduction`](./labs/vault/introduction/): Ansible Vault: encrypt your first secrets file
- [`vault-chiffrer-fichier-variable`](./labs/vault/chiffrer-fichier-variable/): encrypt_string vs whole-file encryption
- [`vault-id-multiples`](./labs/vault/id-multiples/): Multiple vault-ids: isolate dev, staging and prod
- [`vault-playbooks-mixtes`](./labs/vault/playbooks-mixtes/): Mixed playbooks: main.yml plus vault.yml per group
- [`vault-dans-roles`](./labs/vault/dans-roles/): Vault inside a role: plaintext defaults, encrypted vars
- [`vault-integration-hashicorp`](./labs/vault/integration-hashicorp/): Fetch secrets from HashiCorp Vault or OpenBao
- [`vault-integration-passbolt`](./labs/vault/integration-passbolt/): Fetch secrets from Passbolt

### Execution Environments

ansible-navigator, ansible-builder, a custom EE, the CI pipeline, debugging.

- [`ee-hello`](./labs/ee/hello/): First run inside an Execution Environment
- [`ee-inspection`](./labs/ee/inspection/): Inspect an Execution Environment and pick the right one
- [`ee-builder-custom`](./labs/ee/builder-custom/): Build a custom EE with ansible-builder v3
- [`ee-ci-pipeline`](./labs/ee/ci-pipeline/): CI/CD pipeline for Execution Environments
- [`ee-debug`](./labs/ee/debug/): Debug a broken Execution Environment

### Troubleshooting

Verbosity, the interactive debugger, idempotence and performance.

- [`troubleshooting-verbosite`](./labs/troubleshooting/verbosite/): Verbosity levels and callback plugins
- [`troubleshooting-debugger`](./labs/troubleshooting/debugger/): Interactive debugger: debugger: on_failed
- [`troubleshooting-idempotence-perfs`](./labs/troubleshooting/idempotence-perfs/): Fix broken idempotence and tune performance

### Collections

Discovery, requirements, authoring, CI tests, migrating from a role.

- [`collections-decouvrir`](./labs/collections/decouvrir/): Explore Ansible collections: FQCN and structure
- [`collections-navigator`](./labs/collections/navigator/): Automation content navigator: discover a module in a collection and use it
- [`collections-requirements`](./labs/collections/requirements/): requirements.yml: multi-source install with GPG signatures
- [`collections-creer-custom`](./labs/collections/creer-custom/): Build your own collection with a custom Python module
- [`collections-ci-tests`](./labs/collections/ci-tests/): CI matrix for a collection: ansible-core x Python
- [`collections-migration-role`](./labs/collections/migration-role/): Migrate a standalone role to a collection

### Advanced practices

Versioning your playbooks with Git, ansible-pull in GitOps mode.

- [`pratiques-versionner-git`](./labs/pratiques/versionner-git/): Version your playbooks with Git
- [`pratiques-ansible-pull-gitops`](./labs/pratiques/ansible-pull-gitops/): ansible-pull: GitOps and Edge pattern

### RHCE EX294 exam

Full four-hour exam mocks, 19 tasks each, graded by pytest.

- [`rhce-mock-ex294`](./labs/rhce/mock-ex294/): RHCE EX294 mock exam: 19 tasks in 4 hours
- [`rhce-mock-ex294-2`](./labs/rhce/mock-ex294-2/): Mock RHCE EX294 #2

<!-- LABS_LIST_END -->

## Troubleshooting

| Symptom | Where to look |
| --- | --- |
| `UNREACHABLE` on a managed node | `dsoxlab status`; are the VMs running (`virsh list --all`)? |
| `dsoxlab list-labs` does not show your lab | its `lab.yaml` raises while parsing: it vanishes with no message |
| A test passes "for no reason" | facts cache: `rm -rf .ansible_facts/` |
| A lab fails right after another | inherited state: `dsoxlab clean <lab-id>` |
| Risky lab to play | `mise run snapshot` before, `mise run restore` after |

## Contributing

- Contributions: see [CONTRIBUTING](./CONTRIBUTING.md).
- Conduct: [Code of Conduct](./CODE_OF_CONDUCT.md) · Security: [SECURITY](./SECURITY.md).
- Publishing: [RELEASING](./RELEASING.md) (tar.gz bundles, no PyPI).

A lab is proven **in both directions** before it is merged,
`dsoxlab validate-structure` is green, and the statement exists in English and
in French.

## License

Copyright (c) 2026 Stéphane Robert, https://www.stephane-robert.info

This catalogue is published under the
[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](./LICENSE)
license. You may share and adapt it, including commercially, on two conditions:
credit Stéphane Robert with a link to the blog and state what you changed, and
distribute your contributions under the same license.

> The attribution lives here rather than at the top of `LICENSE`, and that is
> deliberate: GitHub only identifies a license from its **bare official text**.
> A custom header above it makes the whole file unrecognisable, the repository is
> reported as `NOASSERTION`, and Scorecard's License check drops from 10 to 9.

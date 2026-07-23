# Ansible Training — RHCE EX294

**Language:** [English](./README.md) · [Français](./README.fr.md)

[![CI](https://github.com/stephrobert/ansible-training/actions/workflows/ci.yml/badge.svg)](https://github.com/stephrobert/ansible-training/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/stephrobert/ansible-training?label=OpenSSF%20Scorecard)](https://securityscorecards.dev/viewer/?uri=github.com/stephrobert/ansible-training)
[![Plumber compliance](https://score.getplumber.io/github.com/stephrobert/ansible-training.svg)](https://score.getplumber.io/github.com/stephrobert/ansible-training)
[![SLSA 3](https://slsa.dev/images/gh-badge-level3.svg)](https://slsa.dev)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](./LICENSE)

Hands-on **Ansible** training, driven by the
[`dsoxlab`](https://github.com/stephrobert/dsoxlab) CLI. This repository is the
**lab catalog** for the Ansible track of
[blog.stephane-robert.info](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/),
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

Préparation système des managed nodes (jouée par `dsoxlab provision`).

- [`prepare managed nodes`](./labs/bootstrap/prepare-managed-nodes/)

### Découvrir Ansible

Premiers contacts : déclaratif vs impératif, installation, CLI, configuration.

- [`declaratif vs imperatif`](./labs/decouvrir/declaratif-vs-imperatif/)
- [`installation ansible`](./labs/decouvrir/installation-ansible/)
- [`configuration ansible`](./labs/decouvrir/configuration-ansible/)
- [`prise en main cli`](./labs/decouvrir/prise-en-main-cli/)

### Premiers pas

Premier playbook, premiers secrets vault.

- [`premier playbook`](./labs/premiers-pas/premier-playbook/)
- [`ansible vault`](./labs/premiers-pas/ansible-vault/)

### Écrire du code Ansible

Structure d'un play, contrôle d'exécution, variables, Jinja2, conditions, boucles, gestion d'erreurs.

- [`plays et tasks`](./labs/ecrire-code/plays-et-tasks/)
- [`handlers`](./labs/ecrire-code/handlers/)
- [`tags`](./labs/ecrire-code/tags/)
- [`checkmode diff`](./labs/ecrire-code/checkmode-diff/)
- [`variables base`](./labs/ecrire-code/variables-base/)
- [`types collections`](./labs/ecrire-code/types-collections/)
- [`facts magic vars`](./labs/ecrire-code/facts-magic-vars/)
- [`custom facts`](./labs/ecrire-code/custom-facts/)
- [`precedence variables`](./labs/ecrire-code/precedence-variables/)
- [`register set fact`](./labs/ecrire-code/register-set-fact/)
- [`parallelisme strategies`](./labs/ecrire-code/parallelisme-strategies/)
- [`async poll`](./labs/ecrire-code/async-poll/)
- [`delegation`](./labs/ecrire-code/delegation/)
- [`lookups`](./labs/ecrire-code/lookups/)
- [`jinja2 base`](./labs/ecrire-code/jinja2-base/)
- [`filtres jinja essentiels`](./labs/ecrire-code/filtres-jinja-essentiels/)
- [`conditions when`](./labs/ecrire-code/conditions-when/)
- [`boucles loop`](./labs/ecrire-code/boucles-loop/)
- [`boucles with deprecated`](./labs/ecrire-code/boucles-with-deprecated/)
- [`block rescue always`](./labs/ecrire-code/block-rescue-always/)
- [`failed when changed when`](./labs/ecrire-code/failed-when-changed-when/)
- [`ignore errors`](./labs/ecrire-code/ignore-errors/)
- [`any errors fatal`](./labs/ecrire-code/any-errors-fatal/)
- [`filtres jinja avances`](./labs/ecrire-code/filtres-jinja-avances/)
- [`tests jinja`](./labs/ecrire-code/tests-jinja/)
- [`module template`](./labs/ecrire-code/module-template/)
- [`lineinfile vs template`](./labs/ecrire-code/lineinfile-vs-template/)
- [`import include`](./labs/ecrire-code/import-include/)

### Modules fichiers

Manipulation de fichiers : copy, file, blockinfile, lineinfile, replace, fetch, archive.

- [`copy`](./labs/modules-fichiers/copy/)
- [`file`](./labs/modules-fichiers/file/)
- [`blockinfile`](./labs/modules-fichiers/blockinfile/)
- [`lineinfile`](./labs/modules-fichiers/lineinfile/)
- [`replace`](./labs/modules-fichiers/replace/)
- [`fetch`](./labs/modules-fichiers/fetch/)
- [`archive unarchive`](./labs/modules-fichiers/archive-unarchive/)

### Modules paquets

Gestion paquets agnostique (package), options dnf, dépôts RPM.

- [`package`](./labs/modules-paquets/package/)
- [`dnf options`](./labs/modules-paquets/dnf-options/)
- [`yum repository`](./labs/modules-paquets/yum-repository/)

### Modules services

Gestion services systemd et tâches planifiées cron.

- [`systemd`](./labs/modules-services/systemd/)
- [`cron`](./labs/modules-services/cron/)

### Modules utilisateurs

Gestion users, groups, clés SSH, sudoers.

- [`user`](./labs/modules-utilisateurs/user/)
- [`group`](./labs/modules-utilisateurs/group/)
- [`authorized key`](./labs/modules-utilisateurs/authorized-key/)
- [`sudoers`](./labs/modules-utilisateurs/sudoers/)

### Modules RHEL

Spécificités RHEL : firewalld, SELinux, sysctl, mount, parted, filesystem, LVM.

- [`firewalld`](./labs/modules-rhel/firewalld/)
- [`sysctl`](./labs/modules-rhel/sysctl/)
- [`selinux`](./labs/modules-rhel/selinux/)
- [`mount`](./labs/modules-rhel/mount/)
- [`parted`](./labs/modules-rhel/parted/)
- [`filesystem`](./labs/modules-rhel/filesystem/)
- [`lvm storage`](./labs/modules-rhel/lvm-storage/)

### Modules réseau

Téléchargement et appels HTTP : get_url, uri.

- [`get url`](./labs/modules-reseau/get-url/)
- [`uri`](./labs/modules-reseau/uri/)

### Modules diagnostic

Inspection et synchronisation : stat, find, assert/fail, wait_for/pause.

- [`stat`](./labs/modules-diagnostic/stat/)
- [`find`](./labs/modules-diagnostic/find/)
- [`assert fail`](./labs/modules-diagnostic/assert-fail/)
- [`wait for pause`](./labs/modules-diagnostic/wait-for-pause/)

### Inventaires

group_vars/host_vars, patterns d'hôtes, inventaire dynamique libvirt.

- [`statiques`](./labs/inventaires/statiques/)
- [`group vars host vars`](./labs/inventaires/group-vars-host-vars/)
- [`patterns hotes`](./labs/inventaires/patterns-hotes/)
- [`dynamique kvm`](./labs/inventaires/dynamique-kvm/)

### Rôles

Anatomie d'un rôle, variables, handlers, argument_specs, consommation, dépendances, rôles système RHEL.

- [`creer premier role`](./labs/roles/creer-premier-role/)
- [`variables defaults vars`](./labs/roles/variables-defaults-vars/)
- [`handlers meta`](./labs/roles/handlers-meta/)
- [`argument specs`](./labs/roles/argument-specs/)
- [`consommer role`](./labs/roles/consommer-role/)
- [`dependencies`](./labs/roles/dependencies/)
- [`system roles`](./labs/roles/system-roles/)

### Tests Molecule

Cycle TDD avec Molecule, scénarios multi-distro.

- [`introduction`](./labs/molecule/introduction/)
- [`installation config`](./labs/molecule/installation-config/)
- [`tdd cycle`](./labs/molecule/tdd-cycle/)
- [`scenarios multi distro`](./labs/molecule/scenarios-multi-distro/)

### Tests Python & lint

testinfra, tox multi-version, ansible-lint profil production.

- [`testinfra`](./labs/tests/testinfra/)
- [`tox multiversion`](./labs/tests/tox-multiversion/)
- [`ansible lint production`](./labs/tests/ansible-lint-production/)

### CI/CD

Pipelines GitHub Actions et GitLab CI pour rôles et collections.

- [`github actions`](./labs/ci/github-actions/)
- [`gitlab`](./labs/ci/gitlab/)

### Galaxy & publication

ansible-galaxy CLI, requirements.yml, audit de rôles tiers, versioning et publication.

- [`ansible galaxy cli`](./labs/galaxy/ansible-galaxy-cli/)
- [`installer roles`](./labs/galaxy/installer-roles/)
- [`auditer role existant`](./labs/galaxy/auditer-role-existant/)
- [`versionner publier`](./labs/galaxy/versionner-publier/)

### Ansible Vault

Vault complet : encrypt_string, vault-id multiples, mixtes, dans rôles, intégration HashiCorp/Passbolt.

- [`introduction`](./labs/vault/introduction/)
- [`chiffrer fichier variable`](./labs/vault/chiffrer-fichier-variable/)
- [`id multiples`](./labs/vault/id-multiples/)
- [`playbooks mixtes`](./labs/vault/playbooks-mixtes/)
- [`dans roles`](./labs/vault/dans-roles/)
- [`integration hashicorp`](./labs/vault/integration-hashicorp/)
- [`integration passbolt`](./labs/vault/integration-passbolt/)

### Execution Environments

ansible-navigator, ansible-builder, EE custom, pipeline CI, debug.

- [`hello`](./labs/ee/hello/)
- [`inspection`](./labs/ee/inspection/)
- [`builder custom`](./labs/ee/builder-custom/)
- [`ci pipeline`](./labs/ee/ci-pipeline/)
- [`debug`](./labs/ee/debug/)

### Troubleshooting

Verbosité, debugger interactif, idempotence et performance.

- [`verbosite`](./labs/troubleshooting/verbosite/)
- [`debugger`](./labs/troubleshooting/debugger/)
- [`idempotence perfs`](./labs/troubleshooting/idempotence-perfs/)

### Collections

Découverte, requirements, création, CI tests, migration depuis un rôle.

- [`decouvrir`](./labs/collections/decouvrir/)
- [`navigator`](./labs/collections/navigator/)
- [`requirements`](./labs/collections/requirements/)
- [`creer custom`](./labs/collections/creer-custom/)
- [`ci tests`](./labs/collections/ci-tests/)
- [`migration role`](./labs/collections/migration-role/)

### Pratiques avancées

Versionner ses playbooks avec Git, ansible-pull mode GitOps.

- [`versionner git`](./labs/pratiques/versionner-git/)
- [`ansible pull gitops`](./labs/pratiques/ansible-pull-gitops/)

### Examen RHCE EX294

Mocks examen complets 4h, 19 tâches chacun, validées par pytest.

- [`mock ex294`](./labs/rhce/mock-ex294/)
- [`mock ex294 2`](./labs/rhce/mock-ex294-2/)

<!-- LABS_LIST_END -->

## Troubleshooting

| Symptom | Where to look |
| --- | --- |
| `UNREACHABLE` on a managed node | `dsoxlab status`; are the VMs running (`virsh list --all`)? |
| `dsoxlab list-labs` does not show your lab | its `lab.yaml` raises while parsing: it vanishes with no message |
| A test passes "for no reason" | facts cache: `rm -rf .ansible_facts/` |
| A lab fails right after another | inherited state: `dsoxlab clean <lab-id>` |
| Risky lab to play | `mise run snapshot` before, `mise run restore` after |

## Contributing & license

- Contributions: see [CONTRIBUTING](./CONTRIBUTING.md).
- Conduct: [Code of Conduct](./CODE_OF_CONDUCT.md) · Security: [SECURITY](./SECURITY.md).
- Publishing: [RELEASING](./RELEASING.md) (tar.gz bundles, no PyPI).
- License: [CC BY-SA 4.0](./LICENSE).

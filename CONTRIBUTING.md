# Contributing to ansible-training

**Language:** [English](./CONTRIBUTING.md) · [Français](./CONTRIBUTING.fr.md)

This repository is a **lab catalog** consumed by the
[`dsoxlab`](https://github.com/stephrobert/dsoxlab) CLI. Contributions are new
labs, fixes, and translations. The CLI itself lives in its own repository: do not
add engine code here.

> **Migration in progress.** The catalog is currently moving to the dsoxlab 0.1.6
> contract (a `lab.yaml` per lab, `setup.yaml` / `cleanup.yaml`, infrastructure
> declared in `meta.yml`). This document describes the target contract. Until the
> migration lands, new lab contributions are on hold: please open an issue rather
> than a PR so we can agree on scope together.

## Setup

```bash
uv tool install dsoxlab        # the CLI (external tool)
git clone <this-repo-url> ansible-training
cd ansible-training
dsoxlab doctor                 # check your environment
dsoxlab provision              # bring up the lab's managed nodes
```

## The golden rule: validation proves state

A lab's tests must assert **the state of the managed nodes**, never that a
playbook was written or a command was typed. The service is running *and*
enabled; the deployed file has the right content *and* the right owner; the
package is installed *and* the repository is declared.

A second requirement is specific to Ansible: **idempotence**. A lab whose
solution playbook still reports `changed` on a second run is a broken lab. This
is what fails RHCE candidates, so the tests must prove it, not hope for it.

## Anatomy of a lab

```text
labs/<section>/<lab>/
├── lab.yaml            # the contract (id, level, runtime, validation…)
├── lab.fr.yaml         # optional: French override of title/description ONLY
├── README.md
├── scenario.md         # scenario.fr.md for the French version
├── setup.yaml          # starting state applied to the managed nodes
├── cleanup.yaml        # reset between two runs
└── challenge/
    ├── README.md       # the mission, no step-by-step
    ├── hints.yaml      # cost-weighted hints
    └── tests/test_functional.py    # the proof: system state
solution/…              # reference solution, encrypted with ansible-vault
```

Playbooks target the groups dsoxlab injects into the inventory: `lab_target` for
the primary host, and `lab_<role>` for every role declared under
`runtime.targets[].roles`. Never hard-code an FQDN.

## Proposing a lab

- **Start from a capability, not a module.** Describe a demonstrable capability
  ("deploy a vhost and prove it survives a replay of the playbook"), open an
  issue, and agree on scope before writing.
- **Pick the runtime the subject demands:** `vm` as soon as real managed nodes
  are needed (services, packages, users, network, storage); `shell` only for what
  stays local to the control node (writing YAML, a Jinja2 template, an
  inventory).
- Point `doc_url` at the real guide the lab makes the learner practice.

## Solutions stay encrypted

Reference solutions live under `solution/`, **encrypted with `ansible-vault`**.
Never commit a solution in clear text, nor the `.vault-pass` file. A clear-text
solution in a PR is an automatic rejection: it spoils the lab for everyone.

## Local checks (before opening a PR)

```bash
dsoxlab list-labs              # does your lab show up? if not, lab.yaml is invalid
dsoxlab validate-structure     # the meta.yml + lab.yaml contract
dsoxlab check <lab-id>         # run the lab's tests
ansible-lint                   # production profile (see .ansible-lint)
```

In that order, with `list-labs` first: a `lab.yaml` that raises while parsing
**silently** disappears from the catalog, and `validate-structure` only validates
labs that were already discovered. A lab missing from `list-labs` is almost
always an invalid `lab.yaml`.

## Conventions

- **Lab id:** `<section>-<slug>` (e.g. `decouvrir-installation-ansible`), for a
  `labs/<section>/<slug>/` directory.
- **Commits:** `feat(<lab>): …`, `fix: …`, `docs: …`, `test: …`.
- **i18n:** `lab.fr.yaml` overrides `title` and `description` only, nothing else.

## Pull requests

Work on a dedicated branch, keep `dsoxlab validate-structure` green, write a
clear description, and link the capability or issue it addresses.

# Changelog

**Language:** [English](./CHANGELOG.md) · [Français](./CHANGELOG.fr.md)

All notable changes to this project are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/), and the project follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Bilingual governance (EN/FR): `CONTRIBUTING`, `CODE_OF_CONDUCT`, `SECURITY`,
  `RELEASING`, `CHANGELOG`, aligned with the reference repository
  `linux-dsoxlab-training`.

### Removed

- **Vendored `dsoxlab` CLI** (`dsoxlab/` + `bin/dsoxlab`): replaced by the
  external CLI (`uv tool install dsoxlab`). The bundled pytest plugin recorded
  nothing (its hook was a no-op); progress tracking is now handled by
  `dsoxlab check`.

### Changed

- **Catalog overhaul**: the 14 historical course chapters
  (`00-Introduction-Ansible` through `13-Taches-Asynchrones`) are replaced by a
  `labs/<section>/<lab>/` hierarchy of 108 labs across 23 sections, covering
  RHCE EX294 2026.
- `.gitignore`: dsoxlab runtime state (`.dsoxlab-context.json`, `.dsoxlab.db`),
  learner workdirs, and Terraform leftovers are no longer versioned.

### Fixed

- **`vault/dans-roles`**: the reference solution never created
  `roles/secured_app/vars/main.yml`, the encrypted file the challenge asks the
  learner to write. It is gitignored on purpose (shipping it would hand out the
  answer, since the lab distributes the password that opens it), so the solution
  now recreates it at run time, encrypted with the lab vault. It also switches
  from `roles:` to `include_role`: Ansible compiles a play's roles when the
  playbook is *loaded*, hence before the file exists. The lab failed on
  `'vault_secured_app_db_password' is undefined`, taking all 6 of its tests with
  it.
- **`vault/playbooks-mixtes`**: same gap, on the inventory side. The solution now
  writes `group_vars/all/vault.yml` and `group_vars/webservers/vault.yml`
  encrypted, then loads them through `vars_files` — group_vars are read when the
  inventory loads, and `meta: refresh_inventory` does not pick up files created
  afterwards (verified). The failure was invisible (`no_log: true` censors the
  message) and cost 5 tests.
- **`inventaires/dynamique-kvm`**: `libvirt-python` is now installed alongside
  `ansible-core` (`uvx_args` in `mise.toml`). The `community.libvirt.libvirt`
  inventory plugin imports it from the **controller** interpreter; without it
  the plugin returns no host at all, the playbook exits on
  `skipping: no hosts matched`, and the 10 tests of the lab fail without a
  single message naming libvirt. The collection was declared in
  `requirements.yml`, the Python library it imports was declared nowhere.

### In progress

- **Migration to the dsoxlab 0.1.6 contract**: the repository still vendors a
  local, read-only `dsoxlab` CLI and drives its infrastructure with
  `virt-install` scripts. The target is the external CLI
  (`uv tool install dsoxlab`) with a `lab.yaml` per lab, `setup.yaml` /
  `cleanup.yaml` playbooks, and infrastructure declared in `meta.yml`. Until the
  migration lands, new lab contributions are on hold.

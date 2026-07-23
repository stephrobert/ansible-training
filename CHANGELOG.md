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

### In progress

- **Migration to the dsoxlab 0.1.6 contract**: the repository still vendors a
  local, read-only `dsoxlab` CLI and drives its infrastructure with
  `virt-install` scripts. The target is the external CLI
  (`uv tool install dsoxlab`) with a `lab.yaml` per lab, `setup.yaml` /
  `cleanup.yaml` playbooks, and infrastructure declared in `meta.yml`. Until the
  migration lands, new lab contributions are on hold.

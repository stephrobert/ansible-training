# Changelog — rôle webserver

## [1.2.0] - 2026-04-26

### Added
- Support multi-distribution (RHEL, AlmaLinux, Debian via vars/<os_family>.yml)
- Variable `webserver_worker_processes` configurable
- Validation argument_specs.yml

### Changed
- Module `package` (agnostique) au lieu de `dnf` direct
- Templates Jinja réorganisés pour lisibilité

### Fixed
- Idempotence handlers (Reload nginx déclenché 2× résolu)

## [1.1.0] - 2026-03-15

### Added
- Handlers Restart nginx et Reload nginx
- Validate sur le template nginx.conf

## [1.0.0] - 2026-02-01

### Added
- Premier release stable
- Installation nginx, démarrage, ouverture firewall HTTP

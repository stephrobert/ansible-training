# Journal des modifications

**Langue :** [English](./CHANGELOG.md) · [Français](./CHANGELOG.fr.md)

Tous les changements notables de ce projet sont consignés dans ce fichier. Le
format s'appuie sur [Keep a Changelog](https://keepachangelog.com/), et le projet
suit le [versionnage sémantique](https://semver.org/lang/fr/).

## [Non publié]

### Ajouté

- Gouvernance bilingue (EN/FR) : `CONTRIBUTING`, `CODE_OF_CONDUCT`, `SECURITY`,
  `RELEASING`, `CHANGELOG`, alignée sur le dépôt de référence
  `linux-dsoxlab-training`.

### Supprimé

- **CLI `dsoxlab` embarquée** (`dsoxlab/` + `bin/dsoxlab`) : remplacée par la CLI
  externe (`uv tool install dsoxlab`). Le plugin pytest local qui l'accompagnait
  n'enregistrait rien (son hook était inopérant) ; le suivi d'avancement est
  désormais assuré par `dsoxlab check`.

### Modifié

- **Refonte du catalogue** : les 14 chapitres pédagogiques historiques
  (`00-Introduction-Ansible` à `13-Taches-Asynchrones`) sont remplacés par une
  hiérarchie `labs/<section>/<lab>/` de 108 labs répartis en 23 sections,
  couvrant le RHCE EX294 2026.
- `.gitignore` : l'état runtime de dsoxlab (`.dsoxlab-context.json`,
  `.dsoxlab.db`), les workdirs apprenant et les vestiges Terraform ne sont plus
  versionnés.

### En cours

- **Migration vers le contrat dsoxlab 0.1.6** : le dépôt embarque encore une CLI
  `dsoxlab` locale (lecture seule) et pilote son infra par des scripts
  `virt-install`. La cible est la CLI externe (`uv tool install dsoxlab`) avec un
  `lab.yaml` par lab, des playbooks `setup.yaml` / `cleanup.yaml`, et l'infra
  déclarée dans `meta.yml`. Tant que la migration n'est pas terminée, les
  contributions de nouveaux labs sont mises en attente.

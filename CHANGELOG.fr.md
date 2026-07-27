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

### Corrigé

- **`vault/dans-roles`** : la solution de référence ne créait jamais
  `roles/secured_app/vars/main.yml`, le fichier chiffré que le challenge demande
  à l'apprenant d'écrire. Il est gitignoré à dessein (le livrer donnerait la
  réponse, puisque le lab distribue le mot de passe qui l'ouvre) : la solution le
  recrée donc à l'exécution, chiffré au vault du lab. Elle passe aussi de
  `roles:` à `include_role` : Ansible compile les rôles d'un play au
  *chargement* du playbook, donc avant que le fichier n'existe. Le lab échouait
  sur `'vault_secured_app_db_password' is undefined`, entraînant ses 6 tests.
- **`vault/playbooks-mixtes`** : même manque, côté inventaire. La solution écrit
  désormais `group_vars/all/vault.yml` et `group_vars/webservers/vault.yml`
  chiffrés, puis les charge par `vars_files` : les group_vars sont lues au
  chargement de l'inventaire, et `meta: refresh_inventory` ne rattrape pas des
  fichiers créés après (vérifié). L'échec était invisible (`no_log: true` censure
  le message) et coûtait 5 tests.
- **`inventaires/dynamique-kvm`** : `libvirt-python` est désormais installé avec
  `ansible-core` (`uvx_args` dans `mise.toml`). Le plugin d'inventaire
  `community.libvirt.libvirt` l'importe depuis l'interpréteur du **contrôleur** ;
  sans lui, le plugin ne remonte aucun hôte, le playbook sort en
  `skipping: no hosts matched`, et les 10 tests du lab tombent sans qu'un seul
  message ne parle de libvirt. La collection était déclarée dans
  `requirements.yml`, la bibliothèque Python qu'elle importe ne l'était nulle
  part.

### En cours

- **Migration vers le contrat dsoxlab 0.1.6** : le dépôt embarque encore une CLI
  `dsoxlab` locale (lecture seule) et pilote son infra par des scripts
  `virt-install`. La cible est la CLI externe (`uv tool install dsoxlab`) avec un
  `lab.yaml` par lab, des playbooks `setup.yaml` / `cleanup.yaml`, et l'infra
  déclarée dans `meta.yml`. Tant que la migration n'est pas terminée, les
  contributions de nouveaux labs sont mises en attente.

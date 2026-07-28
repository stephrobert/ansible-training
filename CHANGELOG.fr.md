# Journal des modifications

**Langue :** [English](./CHANGELOG.md) · [Français](./CHANGELOG.fr.md)

Tous les changements notables de ce projet sont consignés dans ce fichier. Le
format s'appuie sur [Keep a Changelog](https://keepachangelog.com/), et le projet
suit le [versionnage sémantique](https://semver.org/lang/fr/).

## [Non publié]

### Ajouté

- **`vault/integration-passbolt` déclare ses deux conteneurs.** MariaDB et
  Passbolt CE sont montés par dsoxlab (>= 0.1.39), dans l'ordre : la base
  d'abord, avec `ready_exec: healthcheck.sh --connect` comme sonde, si bien que
  Passbolt ne démarre jamais contre une base qui n'accepte pas encore de
  connexion. L'application la joint par le nom `db`, les services d'un dépôt
  partageant un réseau Docker. `setup-passbolt.sh`, qui créait lui-même un
  réseau podman faute de mieux, disparaît.

  Trois détails trouvés en exécutant, pas en relisant : `su` sans `-s /bin/sh`
  sort sur « This account is currently not available » (le compte `www-data` a
  `nologin` pour shell) ; `register_user` n'est pas idempotent et sort en 1 au
  second démarrage, alors que `post_start` est rejoué à chaque `run` ; et le
  port publié ne prouve rien, d'où une sonde `curl` sur le healthcheck.

  Les tests du lab continuent de skipper en campagne, et c'est normal :
  compléter l'inscription, générer la clé OpenPGP et exporter la clé privée
  passent par un humain — c'est l'exercice.

- **`vault/integration-hashicorp` monte son propre serveur.** Le lab déclare son
  Vault dans `runtime.services` (dsoxlab ≥ 0.1.38) : `dsoxlab run` le démarre,
  attend qu'il réponde (`ready_exec: vault status`), y pose `secret/lab82`
  (`post_start`), et `dsoxlab clean` l'arrête. Le `setup-vault.sh` que
  l'apprenant devait lancer à la main disparaît — avec lui disparaît le lab qui
  se skippe en silence chez qui l'a oublié.

  Le serveur écoute sur **8201**, pas sur le 8200 par défaut : c'est ce qui lui
  permet de cohabiter avec le Vault d'une autre formation, dont la présence
  suffisait à faire échouer ce lab.

- **Le conftest monte les services déclarés par un lab.** `dsoxlab run` le fait
  pour l'apprenant, mais la campagne formateur lance pytest directement : sans
  ce crochet, un lab à service se skippe à chaque campagne, et ses dépendances
  ne sont jamais exercées. Sans effet pour les 112 autres labs.

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

- **Le lab Vault reconnaît son propre serveur.** Son garde-fou testait « un port
  répond », ce qui ne prouve rien sur le port par défaut de Vault : le conteneur
  `dsoxlab-terraform-training-vault` d'une autre formation écoutait là, le
  module a donc cessé de se skipper, et ses quatre tests ont échoué sur
  `Forbidden: Permission Denied to path ['lab82']`. Il exige désormais les deux
  marques de son serveur — token accepté et `secret/lab82` présent — et skippe
  en nommant la cause. La vérification passe d'un `pytest.skip` de module à une
  fixture : un skip de module s'évalue à l'IMPORT, donc avant que le conftest
  n'ait monté le service.
- **`community.hashi_vault` et `anatomicjc.passbolt` déclarées** dans
  `requirements.yml`, et **`hvac` attaché à ansible-core** (`uvx_args` du
  `mise.toml`), comme `libvirt-python`. Les labs les importaient sans que rien
  ne les déclare : leurs tests se skippant faute de serveur, l'absence n'a
  jamais été signalée. Un skip conditionnel masque une dépendance manquante
  aussi bien qu'il masque un service absent.
- **Les 4 labs de la section `molecule/` étaient exclus de la campagne.**
  `norecursedirs = ["molecule", …]` matche un nom de répertoire à n'importe
  quelle profondeur : écrit pour les scénarios `labs/*/*/molecule/`, il
  emportait la section entière. 30 tests ne tournaient pas pendant que le script
  annonçait « 113 labs ». Les scénarios internes restent exclus par le
  `collect_ignore_glob` du conftest, qui est ancré sur le chemin.
- **`mise run test-all` vérifie que l'infra est debout** avant de jouer quoi que
  ce soit. Le script exigeait déjà `.vault-pass` et un catalogue non vide, mais
  pas les VM : une infra détruite se traduisait par des centaines d'erreurs de
  connexion accusant les labs, au bout de plusieurs minutes. Il s'arrête
  désormais en quelques secondes avec la marche à suivre.
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

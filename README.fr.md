# Ansible Training — RHCE EX294

**Langue :** [English](./README.md) · [Français](./README.fr.md)

[![CI](https://github.com/stephrobert/ansible-training/actions/workflows/ci.yml/badge.svg)](https://github.com/stephrobert/ansible-training/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/stephrobert/ansible-training?label=OpenSSF%20Scorecard)](https://securityscorecards.dev/viewer/?uri=github.com/stephrobert/ansible-training)
[![Plumber compliance](https://score.getplumber.io/github.com/stephrobert/ansible-training.svg)](https://score.getplumber.io/github.com/stephrobert/ansible-training)
[![SLSA 3](https://slsa.dev/images/gh-badge-level3.svg)](https://slsa.dev)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](./LICENSE)

Formation **Ansible** pratique, pilotée par la CLI
[`dsoxlab`](https://github.com/stephrobert/dsoxlab). Ce dépôt est le **catalogue
de labs** de la formation Ansible de
[blog.stephane-robert.info](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/),
orientée certification **RHCE (EX294)**, avec l'idempotence comme fil rouge.

## Ce que c'est

`ansible-training` est un **dépôt de contenu**, pas une application. Il fournit :

- des **labs guidés**, avec des instructions précises,
- des **challenges** sans pas-à-pas, pour vérifier l'autonomie,
- un **examen blanc** EX294 qui synthétise l'ensemble,
- une **validation automatisée** qui prouve l'état des managed nodes (et non
  qu'un playbook a été écrit),
- un **scoring** avec des indices à coût variable.

La CLI `dsoxlab` est le point d'entrée unique : elle prépare un lab, affiche la
mission, valide, note et rend compte. Elle vit dans **son propre dépôt** et
s'installe **séparément** : elle ne fait pas partie de ce dépôt.

## Pré-requis

- Python 3.11+ et [`uv`](https://docs.astral.sh/uv/)
- [`mise`](https://mise.jdx.dev/) pour la chaîne Ansible (voir ci-dessous)
- `git`
- **KVM/libvirt** : les labs ont besoin de 4 VMs AlmaLinux 9 (1 control node,
  3 managed nodes). Comptez ~6 Go de RAM et ~55 Go de disque.

## Installation

```bash
# 1. La CLI dsoxlab (outil externe, hors de ce dépôt)
uv tool install dsoxlab        # ou : pipx install dsoxlab

# 2. Ce catalogue de labs
git clone https://github.com/stephrobert/ansible-training.git
cd ansible-training

# 3. La chaîne Ansible, aux versions de l'examen
mise install                   # ansible-core 2.18, ansible-lint, molecule, yamllint

# 4. Les 4 VMs, préparées (~5 min)
mise run provision

# 5. Parcourir et jouer
dsoxlab list-labs
dsoxlab run <id-du-lab>
dsoxlab check <id-du-lab>
```

### Ton premier lab

**Commence par la section `decouvrir`.** `bootstrap` prépare l'infrastructure,
elle n'est pas le point d'entrée pédagogique.

```bash
dsoxlab use decouvrir                 # section de départ
dsoxlab next                          # → decouvrir-declaratif-vs-imperatif
```

Puis, pour ce lab comme pour tous les autres, le même cycle en quatre temps :

```bash
dsoxlab course <id>        # 1. le contexte, puis le cours
dsoxlab challenge <id>     # 2. ce qui t'est demandé
dsoxlab run <id>           # 3. prépare ton espace de travail et t'y place
dsoxlab check <id>         # 4. valide et note
```

`run` est l'étape que l'on oublie : c'est elle qui crée les fichiers sur
lesquels tu travailles, et pour un lab `vm`, qui met les managed nodes dans
l'état décrit par le scénario. Un `check` lancé sans `run` échoue en annonçant
que rien n'est fait, ce qui est vrai mais trompeur.

**Les 25 labs `shell` ne demandent aucune machine virtuelle** : écrire du YAML,
un template Jinja2, un inventaire, jouer Molecule ou `ansible-lint` se fait sur
ton poste. Tu peux donc commencer sans provisionner quoi que ce soit, et ne
monter les 4 VMs qu'au moment d'aborder les labs `vm`.

> ⚠️ **`mise run provision`, et non `dsoxlab provision` seul.** La CLI monte les
> VMs, mais elle les livre **nues** : cloud-init pose le compte et la clé, rien
> de plus. Les labs, eux, ciblent des managed nodes équipés (`firewalld`,
> `python3-firewall`, `chrony`). Sans cette préparation, tout lab touchant au
> pare-feu échoue sur « Failed to import the required Python library (firewall) ».
> La tâche `mise` enchaîne le provisioning et l'amorçage.
>
> Pour rejouer la seule préparation : `mise run bootstrap-nodes`.

`dsoxlab doctor` vérifie l'environnement (Python, pytest, runtimes, labs
détectés). `mise run setup-hosts` et `mise run setup-ssh` rendent les noms du lab
résolvables et configurent SSH pour utiliser la clé du dépôt.

**Pourquoi `mise` en plus de `dsoxlab`** : la version d'`ansible-core` fait
partie de l'exercice. Un playbook qui passe en 2.18 peut échouer en 2.19, et
l'EX294 se passe sur une version précise. `mise` la pin, avec la chaîne de lint
qui va avec. `dsoxlab`, lui, ne pilote que les labs.

### Rester à jour

Les labs arrivent dans ce dépôt, la CLI évolue de son côté. Mettez chacun à jour
séparément :

```bash
git pull                       # nouveaux labs
uv tool upgrade dsoxlab        # la CLI (ou : pipx upgrade dsoxlab)
mise install                   # la chaîne Ansible si les versions ont bougé
```

Votre travail en cours vit dans le `challenge/` de chaque lab et n'est pas
versionné : `git pull` apporte les nouveaux labs sans jamais y toucher.

## Comment ça marche

### Le contrat déclaratif (deux niveaux)

Le catalogue est décrit par des données, pas par du code : le moteur `dsoxlab`
reste neutre vis-à-vis du domaine et lit deux niveaux de fichiers.

- **`meta.yml`** à la racine déclare l'identité du dépôt, la topologie
  d'infrastructure (réseau, hôtes, provider) et l'**ordre** des sections
  qu'affiche `list-labs`.
- **`lab.yaml`** par lab (sous `labs/<section>/<lab>/`) déclare ses `skills`,
  son `level`, son `runtime` (`vm` ou `shell`, avec les hôtes visés), ses
  `distros`, son `doc_url` et un bloc `validation`. Un `lab.fr.yaml` optionnel
  surcharge le `title` et la `description` en français.

`dsoxlab validate-structure` vérifie le contrat des labs **découverts** :
fichiers requis présents, métadonnées complètes, cohérence des cibles. Attention,
il ne signale pas un lab déclaré dans `meta.yml` mais absent du disque : la
découverte se fait par un glob sur `labs/**/lab.yaml`, et un `lab.yaml` invalide
disparaît **silencieusement** du catalogue. D'où la règle : `dsoxlab list-labs`
d'abord, `validate-structure` ensuite.

### Le cycle de vie d'un lab

L'apprenant pilote tout par la CLI :

```bash
dsoxlab doctor                        # vérifier l'environnement
dsoxlab list-labs                     # parcourir le catalogue
dsoxlab show <id>                     # métadonnées et statut d'un lab
dsoxlab run <id>                      # préparer et démarrer l'environnement
dsoxlab challenge <id>                # lire la mission (sans pas-à-pas)
dsoxlab hint <id>                     # révéler un indice (déduit du score)
dsoxlab check <id>                    # jouer les tests, calculer et noter
dsoxlab submit <id>                   # soumission finale, clôt la session
dsoxlab progress                      # avancement par section, score moyen
```

`run` est le moment où l'environnement se monte. Pour un lab **shell**, la CLI
crée le `workdir` et copie les fixtures déclarées. Pour un lab **vm**, elle joue
le `setup.yaml` du lab sur les managed nodes et ouvre un accès au control node,
là où vous écrivez vos playbooks.

### Topologie

Réseau libvirt dédié `lab-ansible` (10.10.20.0/24), pour cohabiter avec les
autres labs sans collision.

| Hôte | Rôle | RAM | vCPU |
| --- | --- | --- | --- |
| `control-node.lab` | control node : vous y écrivez vos playbooks | 2048 | 2 |
| `web1.lab` | managed node | 1024 | 1 |
| `web2.lab` | managed node | 1024 | 1 |
| `db1.lab` | managed node | 1536 | 1 |

Les IP ne sont pas déclarées : Terraform les attribue et l'inventaire les lit.
`dsoxlab` injecte à l'exécution les groupes que ciblent les playbooks des labs :
`lab_target` (le control node), `lab_<role>` (un par managed node utilisé) et
`labenv` (tous). Un lab ne code jamais un FQDN en dur.

### Les comptes : `ansible` (service) et `student` (humain)

Le cloud-init pose **deux comptes** sur chaque nœud, tous deux durcis de la même
façon : connexion par **clé SSH uniquement** (`ssh_pwauth: false`), **aucun mot de
passe de login**, et `sudo NOPASSWD:ALL`.

- **`ansible`** : le compte de **service** par lequel toute l'automatisation se
  connecte, dsoxlab comme les playbooks des labs. C'est le `ansible_user` de
  l'inventaire et l'utilisateur du `ssh_config` généré. Se connecter via un compte
  de service dédié, distinct de l'humain, est la **bonne pratique** : les actions
  d'automatisation sont attribuables et le compte se révoque indépendamment. Son
  `NOPASSWD:ALL` est assumé : une automatisation RHCE touche à tout (dnf, systemd,
  LVM, SELinux, firewalld) ; la sécurité tient à la **dédicace** du compte, pas à
  un `sudo` bridé qui casserait l'automatisation.
- **`student`** : le compte **humain**, celui depuis lequel vous lancez `dsoxlab`
  et `ansible` sur le control node. Il existe aussi sur les managed nodes pour le
  debug, mais ce n'est **jamais** lui qui pilote l'automatisation.

Conséquence pratique : quand un lab restreint l'accès SSH (`AllowUsers`) ou fixe un
`remote_user`, c'est **`ansible`** qu'il vise ; restreindre à un autre compte
couperait la connexion de l'automatisation. Pour inspecter un nœud à la main,
`dsoxlab ssh <host>` vous y connecte avec le compte `ansible`.

### Runtimes

| Runtime | Ce qu'il apporte |
| --- | --- |
| `vm` | Terraform + libvirt. Les vrais managed nodes : services, paquets, utilisateurs, stockage, et la **persistance après reboot**. 88 labs. |
| `shell` | Ce qui reste local au poste : écrire du YAML, un template Jinja2, un inventaire, jouer Molecule ou ansible-lint. 25 labs. |

Les VMs se provisionnent une fois avec `dsoxlab provision` et se détruisent avec
`dsoxlab destroy`.

### Le modèle de validation

La validation **prouve l'état du système, elle ne fait pas confiance**. Chaque
lab livre des tests `pytest` / `pytest-testinfra` sous `challenge/tests/` qui
vérifient des faits sur la machine : le service tourne **et** est activé, le
fichier déployé a le bon contenu **et** le bon propriétaire. Un test qui se
contente de vérifier qu'une commande a été tapée est refusé.

Deuxième exigence, propre à Ansible : **l'idempotence**. Un lab dont la solution
rejouée annonce encore des `changed` est un lab faux. C'est le piège qui fait
échouer les candidats RHCE, donc les tests le prouvent quand le sujet le
justifie.

- En mode formateur, une fixture du `conftest.py` racine **rejoue la solution de
  référence** avant les tests, pour prouver que la solution elle-même est juste.
- Dans `dsoxlab check` (le chemin de l'apprenant), ce rejeu est **désactivé**
  (`LAB_NO_REPLAY=1`) : les tests valident son propre travail.

### Scoring, indices, avancement

`check` enregistre un score (tests passés sur total, moins le coût des indices
utilisés). Les indices sont **à coût variable** : en révéler un retire des
points, d'où leur caractère volontaire. L'historique vit dans une base SQLite
locale au dépôt (`.dsoxlab.db`, non versionnée) ; `dsoxlab scores` et
`dsoxlab progress` la lisent.

### Les solutions restent chiffrées

Les solutions de référence vivent dans `solution/`, **chiffrées avec
`ansible-vault`**. Une solution en clair spoile le lab pour tout le monde, et
l'historique git la garde même après suppression. Un hook `pre-commit` vérifie
l'en-tête de chiffrement à chaque commit plutôt que de faire confiance.

```bash
mise run solutions-status      # vérifie que tout est chiffré
mise run solve <section>/<lab> # pose la solution officielle (formateur)
```

## Catalogue

Les labs vivent sous `labs/` et sont ordonnés par `meta.yml`. La liste ci-dessous
est générée : lancez `python3 scripts/render-readme.py` pour la rafraîchir.

<!-- LABS_LIST_START -->

**113 labs** répartis en **23 sections** (source de vérité : [`meta.yml`](./meta.yml)).

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

## Dépannage

| Symptôme | Piste |
| --- | --- |
| `UNREACHABLE` sur un managed node | `dsoxlab status` ; les VMs tournent-elles (`virsh list --all`) ? |
| `dsoxlab list-labs` ne montre pas votre lab | son `lab.yaml` lève au parsing : il disparaît sans message |
| Un test passe « sans raison » | cache de facts : `rm -rf .ansible_facts/` |
| Un lab échoue après un autre | état hérité : `dsoxlab clean <id-du-lab>` |
| Lab risqué à jouer | `mise run snapshot` avant, `mise run restore` après |

## Contribuer & licence

- Contributions : voir [CONTRIBUTING](./CONTRIBUTING.md).
- Conduite : [Code de conduite](./CODE_OF_CONDUCT.md) · Sécurité : [SECURITY](./SECURITY.md).
- Publication : [RELEASING](./RELEASING.md) (bundles tar.gz, pas de PyPI).
- Licence : [CC BY-SA 4.0](./LICENSE).

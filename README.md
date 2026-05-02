# Ansible Training — RHCE 2026

Bienvenue ! Ce dépôt est le **lab pédagogique public** de la formation Ansible
[RHCE EX294 (2026)](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/)
du blog [blog.stephane-robert.info](https://blog.stephane-robert.info).

Vous y trouverez :

- Une **infra reproductible** (4 VMs AlmaLinux 10 sur KVM/libvirt) provisionnée
  en une commande, prête à recevoir vos playbooks.
- **103 labs progressifs** répartis en 23 sections (découvrir, premiers pas,
  écrire du code, modules incontournables, rôles, Molecule, CI/CD, Galaxy,
  Vault, Execution Environments, troubleshooting, collections, mock RHCE).
- Des **tests automatisés** (pytest + testinfra) pour chaque challenge —
  vous savez immédiatement si votre solution est correcte.
- Un **Makefile par lab** pour réinitialiser l'état des managed nodes entre
  deux essais.

---

## 🧭 Sommaire

- [Démarrage rapide](#-démarrage-rapide)
- [Topologie du lab](#-topologie-du-lab)
- [Structure du dépôt](#-structure-du-dépôt)
- [Comment fonctionne un lab](#-comment-fonctionne-un-lab)
- [Lancer les tests pytest](#-lancer-les-tests-pytest)
- [Reset d'un lab](#-reset-dun-lab)
- [Suivi de progression](#-suivi-de-progression)
- [Linter avec `ansible-lint`](#-linter-avec-ansible-lint)
- [Liste des labs](#-liste-des-labs)
- [Pré-requis poste de travail](#-pré-requis-poste-de-travail)
- [Dépannage](#-dépannage)

### Alternative avec Docker

Si vous préférez utiliser Docker plutôt que d'installer Ansible directement sur votre système, nous fournissons une image Docker prête à l'emploi avec tous les outils nécessaires et le lab pré-installé.

#### Prérequis Docker

Assurez-vous d'avoir Docker installé sur votre système :

* **Sur Ubuntu/Debian** :
https://docs.docker.com/engine/install/ubuntu/
https://docs.docker.com/engine/install/linux-postinstall/

* **Sur Fedora** :
https://docs.docker.com/engine/install/fedora/
https://docs.docker.com/engine/install/linux-postinstall/

* **Sur macOS/Windows** : Installez [Docker Desktop](https://www.docker.com/products/docker-desktop/)

#### Construction et utilisation de l'image

1. **Cloner le dépôt** (si ce n'est pas déjà fait) :
   ```bash
   git clone https://github.com/stephrobert/ansible-training.git
   cd ansible-training
   ```

2. **Construire l'image Docker** :
   ```bash
   cd environments/docker
   docker build -t ansible-training .
   ```

3. **Lancer le conteneur interactif** :
   ```bash
   docker run -it --rm ansible-training
   ```

4. **Ou monter un répertoire local pour persister vos modifications** :
   ```bash
   docker run -it --rm -v $(pwd)/../../:/workspace ansible-training
   ```

#### Contenu de l'environnement Docker

L'image Docker inclut :
- **Ansible** (dernière version stable)
- **ansible-lint** pour la validation des playbooks
- **pytest** et **pytest-testinfra** pour les tests
- **Git** pour le versioning
- **Le lab complet** pré-installé dans `/home/lab-user/ansible-training`
- Un utilisateur non-root `lab-user` pour plus de sécurité

#### Avantages de l'approche Docker

- ✅ **Isolation complète** : aucun impact sur votre système hôte
- ✅ **Reproductibilité** : environnement identique pour tous
- ✅ **Prêt à l'emploi** : tous les outils pré-installés et configurés
- ✅ **Multi-plateforme** : fonctionne sur Linux, macOS et Windows
- ✅ **Nettoyage facile** : suppression simple du conteneur

---

## 🚀 Démarrage rapide

Si votre poste est déjà équipé (cf. [Pré-requis](#-pré-requis-poste-de-travail)) :

```bash
git clone https://github.com/stephrobert/ansible-training.git
cd ansible-training

# 1. Installer les outils (1ʳᵉ fois uniquement, ~3 min)
make bootstrap

# 2. Créer les 4 VMs + préparer les managed nodes (~5 min)
make provision

# 3. Rendre les hostnames du lab résolvables localement
make hosts-add        # → ssh web1.lab fonctionne, plus besoin d'IPs

# 4. Configurer SSH pour utiliser la clé du repo automatiquement
make ssh-config-add   # → ssh ansible@web1.lab fonctionne sans -i

# 5. Vérifier la connectivité Ansible (4 "pong" attendus)
make verify-conn

# 6. Voir le prochain lab à attaquer
dsoxlab next          # ou : make dsoxlab-next
```

À ce stade, vos 4 VMs tournent, leurs hostnames sont résolvables, et
Ansible les voit. **Vous pouvez commencer n'importe quel lab** — pas
besoin de les faire dans l'ordre.

### Cycle de vie complet

| Action | Commande | Quand ? |
| --- | --- | --- |
| Installer les outils | `make bootstrap` | 1ʳᵉ fois uniquement |
| Créer les VMs | `make provision` | Au début, après chaque `destroy` |
| Résoudre les hostnames | `make hosts-add` | Après `provision` (ajout `/etc/hosts`) |
| Configurer SSH (clé du repo) | `make ssh-config-add` | Après `provision` (`ssh ansible@web1.lab` sans `-i`) |
| Tester la connectivité | `make verify-conn` | Vérification rapide à tout moment |
| Voir l'avancement | `dsoxlab show` / `dsoxlab next` | Pendant la formation |
| Snapshot (avant lab risqué) | `make snapshot` | Avant un lab destructif |
| Restaurer le snapshot | `make restore` | Après un crash de lab |
| Détruire les VMs | `make destroy` | Fin de formation ou reset complet |
| Nettoyer `/etc/hosts` | `make hosts-remove` | Après `destroy` (cleanup symétrique) |
| Nettoyer la config SSH | `make ssh-config-remove` | Après `destroy` (cleanup symétrique) |

> 💡 **Vous arrivez directement à un lab précis sans avoir fait les
> précédents ?** C'est OK. La seule chose qui compte, c'est que les 4 VMs
> répondent au ping (`make verify-conn`). Chaque lab est **autonome** :
> son `README.md` explique ce qu'il faut savoir, et son `Makefile clean`
> nettoie l'état avant de rejouer.

---

## 🌐 Topologie du lab

| Hôte | IP | Rôle | Groupe(s) |
| --- | --- | --- | --- |
| `control-node.lab` | 10.10.20.10 | Poste Ansible (push SSH) | `control` |
| `web1.lab` | 10.10.20.21 | Web 1 | `webservers`, `rhce_lab` |
| `web2.lab` | 10.10.20.22 | Web 2 | `webservers`, `rhce_lab` |
| `db1.lab` | 10.10.20.31 | Base de données | `dbservers`, `rhce_lab` |

- **Réseau libvirt** : `lab-ansible` (10.10.20.0/24, NAT, baux DHCP statiques par MAC).
- **Auth** : utilisateur `ansible` avec sudo NOPASSWD, clé SSH `ssh/id_ed25519`
  (générée localement, jamais commitée).
- **Provisionning** : cloud-init minimal (user + clé + sudo) ; le reste
  (firewalld, chrony, SELinux, `/etc/hosts`) est appliqué par Ansible
  lui-même via [`labs/bootstrap/prepare-managed-nodes/playbook.yml`](./labs/bootstrap/prepare-managed-nodes/playbook.yml)
  — **« Ansible se prépare lui-même »**.

Pour la liste complète des hôtes, des groupes et la convention de ciblage
(quand viser `db1.lab` vs `webservers` vs `all`), voir aussi
[`meta.yml`](./meta.yml) et la section
[Liste des labs](#-liste-des-labs).

---

## 📂 Structure du dépôt

```text
ansible-training/
├── README.md                    # ce fichier
├── Makefile                     # bootstrap, provision, destroy, snapshot, restore, test-all
├── meta.yml                     # source de vérité de l'ordre des labs (23 sections, 103 labs)
├── ansible.cfg                  # config Ansible (forks, become, result_format=yaml)
├── conftest.py                  # fixture pytest qui rejoue solution.yml avant les tests
├── inventory/hosts.yml          # inventaire YAML : control + webservers + dbservers
├── infra/virt-install/          # provision/destroy + cloud-init templates
├── ee/                          # Execution Environment (image OCI)
├── scripts/                     # bootstrap, lint-all, snapshot-vms, restore-vms, hosts/ssh
├── bin/dsoxlab                  # CLI de suivi de progression
├── dsoxlab/                     # implémentation Python de la CLI
├── solution/                    # solutions formateur chiffrées via ansible-vault
├── ssh/                         # clés SSH générées localement (gitignored)
├── collected/                   # cible des fetch (gitignored)
└── labs/
    ├── bootstrap/prepare-managed-nodes/   # bootstrap système des managed nodes
    ├── decouvrir/                         # 4 labs (déclaratif/impératif, install, config, CLI)
    ├── premiers-pas/                      # 2 labs (premier playbook, vault basics)
    ├── ecrire-code/                       # 28 labs (plays, handlers, vars, Jinja, conditions, …)
    ├── modules-fichiers/                  # 5 labs (copy, file, blockinfile, fetch, archive)
    ├── modules-paquets/ modules-services/ # paquets, systemd, cron
    ├── modules-utilisateurs/ modules-rhel/ modules-reseau/ modules-diagnostic/
    ├── inventaires/ roles/ molecule/ tests/ ci/ galaxy/
    ├── vault/ ee/ troubleshooting/ collections/ pratiques/
    └── rhce/mock-ex294/                   # mock examen EX294 (12 tâches en 4h)
```

Chaque lab `labs/<section>/<lab>/` est **autonome**. Sa structure type :

```text
labs/<section>/<lab>/
├── README.md              # tutoriel guidé (objectifs, exercices, observations)
├── Makefile               # cible `clean` pour reset l'état des managed nodes
└── challenge/
    ├── README.md          # consigne du challenge final + squelette à compléter
    └── tests/
        └── test_*.py      # pytest+testinfra qui valide la solution écrite
```

> ⚠️ **Important** : les fichiers `lab.yml` (tutoriel) et
> `challenge/solution.yml` (challenge) **ne sont pas livrés** — c'est à
> l'apprenant de les écrire à partir des consignes. C'est le cœur de la
> pédagogie de ce dépôt.

---

## 🎓 Comment fonctionne un lab

Un lab pédagogique se déroule en **2 phases** :

### Phase 1 — Tutoriel guidé (`README.md` du lab)

Le `README.md` à la racine du lab contient un **tuto pas-à-pas** :

- **🧠 Rappel** — concept clé + lien vers la page du blog.
- **🎯 Objectifs** — ce que vous saurez faire à la fin.
- **🔧 Préparation** — vérifier que les VMs répondent, nettoyer un état antérieur.
- **📚 Exercices** — vous écrivez `lab.yml` à la racine du lab, étape par étape,
  en suivant les snippets fournis dans le README. Chaque exercice se termine
  par une section **🔍 Observation** qui explique ce que vous devez voir.
- **🤔 Questions de réflexion** — pour ancrer la compréhension.

### Phase 2 — Challenge final (`challenge/README.md`)

Une fois le tuto digéré, le challenge propose une variation autonome :

- **🎯 Objectif** — ce qu'il faut produire.
- **🧩 Indices / Squelette** — le squelette `solution.yml` avec des `???` à
  remplacer par vous.
- **🚀 Lancement** — la commande `ansible-playbook ...`.
- **🧪 Validation automatisée** — `pytest` qui vérifie objectivement votre
  solution.
- **🧹 Reset** — `make clean` pour rejouer à blanc.
- **💡 Pour aller plus loin** — concepts avancés + lint avec `ansible-lint`.

> 💡 **Convention** : `lab.yml` (à la racine du lab) = code du tuto.
> `challenge/solution.yml` = code du challenge. Les deux sont **à écrire par
> l'apprenant**.

### 💻 Configuration recommandée : terminal en deux colonnes

Pour un confort optimal, **dédiez une colonne à la consigne et une autre
aux commandes**. Vous lisez le tutoriel à gauche, vous tapez à droite :

```text
┌─────────────────────────────────┬─────────────────────────────────┐
│  📖  dsoxlab lab decouvrir/...  │  $ ansible all -m ping          │
│                                 │  $ vim lab.yml                  │
│  Lab 01 — Déclaratif vs ...     │  $ ansible-playbook lab.yml     │
│                                 │  ...                            │
│  ## 🎯 Objectifs                │                                 │
│  ...                            │                                 │
└─────────────────────────────────┴─────────────────────────────────┘
              consigne                       actions
```

Au choix selon votre environnement :

| Outil | Comment splitter |
| --- | --- |
| **tmux** *(universel, recommandé)* | `tmux new-session \; split-window -h` puis `Ctrl+b ←/→` pour naviguer |
| **VS Code terminal** | `Ctrl+Shift+5` (split à droite) |
| **Terminator** *(GTK)* | `Ctrl+Shift+E` (split vertical) |
| **Tilix** | `Ctrl+Alt+R` (split à droite) |
| **Konsole** | `Ctrl+(` |
| **Windows Terminal** | `Alt+Shift+D` |
| **iTerm2** *(macOS)* | `Cmd+D` |

Recette **tmux** prête à coller :

```bash
tmux new-session -d -s lab \; \
    send-keys 'dsoxlab lab decouvrir/declaratif-vs-imperatif' C-m \; \
    split-window -h \; \
    attach
# Ctrl+b ← / Ctrl+b → pour passer d'une colonne à l'autre
# Ctrl+b z pour zoomer/dézoomer une colonne
# Ctrl+b d pour détacher (la session reste vivante)
# tmux attach -t lab pour reprendre plus tard
```

> 💡 **Astuce** : laissez tourner `dsoxlab lab xxx` à gauche **sans pager**
> (`--no-pager`) si vous préférez relire le tutoriel en scrollant la sortie
> du terminal plutôt qu'en restant dans `less`.

---

## 🧪 Lancer les tests pytest

Chaque challenge a une suite de tests `pytest + testinfra` qui valide la
solution sur les managed nodes.

```bash
# Un seul lab
pytest -v labs/ecrire-code/block-rescue-always/challenge/tests/

# Toute une section
pytest -v labs/vault/

# Tous les labs (long — selon le nombre de challenges écrits)
pytest -v labs/
```

### La fixture `_apply_lab_state` (autouse)

Le [`conftest.py`](./conftest.py) racine contient une fixture qui **rejoue
automatiquement votre `solution.yml`** avant les tests. Cela garantit :

- Que vos tests passent **indépendamment de l'ordre** dans lequel les labs ont
  été joués manuellement.
- Que l'état des managed nodes correspond bien à ce que la solution attend.

3 cas pris en compte :

| Type de lab | Comportement de la fixture |
| --- | --- |
| Lab démo (Makefile + `playbook.yml` racine) | `make setup` + `ansible-playbook playbook.yml` |
| Lab pédagogique avec `challenge/solution.yml` écrit | `ansible-playbook challenge/solution.yml` (+ `_EXTRA_ARGS` éventuels) |
| Lab pédagogique sans solution | `pytest.skip` avec message clair (« écrivez d'abord `solution.yml` ») |

### Désactiver la fixture

Si vous voulez tester à la main sans qu'Ansible ne rejoue :

```bash
LAB_NO_REPLAY=1 pytest -v labs/ecrire-code/block-rescue-always/challenge/tests/
```

---

## 🧹 Reset d'un lab

Chaque lab a un `Makefile` avec une cible `clean` qui supprime ce qu'il a posé
sur les managed nodes. Indispensable pour rejouer un scénario à blanc.

```bash
make -C labs/ecrire-code/block-rescue-always clean
```

> 💡 **Snapshot global** : si vous voulez revenir à un état VMs neuves :
> `make snapshot` (avant un lab risqué) puis `make restore` (après) — utile
> pour explorer un lab destructif.

---

## 📊 Suivi de progression

Le repo embarque une **CLI Python** (`bin/dsoxlab`) qui inscrit chaque run
`pytest` dans une SQLite locale (`~/.local/share/dsoxlab/progress.db`) et affiche
un dashboard de votre avancement par section/lab.

Le suivi est **automatique** : dès que vous lancez `pytest` sur un lab
(`pytest labs/<section>/<lab>/challenge/tests/`), un plugin pytest interne
inscrit le résultat dans la base.

### Installer la CLI dans le `PATH` (recommandé)

Pour pouvoir taper `dsoxlab` ou `lab` depuis n'importe où sans préfixer
`bin/`, créez un lien symbolique dans un dossier de votre `PATH` :

```bash
# Option A — lien personnel (~/.local/bin doit être dans votre PATH)
mkdir -p ~/.local/bin
ln -sf "$(pwd)/bin/dsoxlab" ~/.local/bin/dsoxlab

# Option B — wrapper qui pointe vers ce repo (utile si plusieurs repos)
cat > ~/.local/bin/dsoxlab <<'EOF'
#!/usr/bin/env bash
exec /home/bob/Projets/ansible-training/bin/dsoxlab "$@"
EOF
chmod +x ~/.local/bin/dsoxlab
```

Vérification :

```bash
which dsoxlab     # /home/<vous>/.local/bin/dsoxlab
dsoxlab show      # plus besoin de bin/dsoxlab
dsoxlab lab decouvrir/installation-ansible
```

> 💡 Si `~/.local/bin` n'est pas dans votre `PATH`, ajoutez à `~/.bashrc`
> ou `~/.zshrc` : `export PATH="$HOME/.local/bin:$PATH"`.

### Commandes principales

```bash
dsoxlab                                          # tableau de bord par section
dsoxlab next                                     # suggère le prochain lab à attaquer
dsoxlab stats                                    # % réussite par section
dsoxlab show --section vault                     # filtrer une section
dsoxlab show --status completed                  # filtrer par statut
dsoxlab lab decouvrir/installation-ansible       # 📖 README rendu Markdown riche (80 col par défaut)
dsoxlab lab vault/introduction --challenge       # 🎯 challenge/README.md rendu
dsoxlab lab vault/introduction --both            # tutoriel + challenge à la suite
dsoxlab lab vault/introduction --width 100       # forcer 100 colonnes (défaut 80, 0 = terminal)
dsoxlab reset --lab vault/introduction -y        # rejouer un lab à blanc
dsoxlab reset --all                              # reset complet (avec confirmation)
dsoxlab export -o my-progress.json                # export JSON pour formateur/agrégation
```

Cibles Make équivalentes (pas besoin du `PATH`) :

```bash
make dsoxlab / dsoxlab-next / dsoxlab-stats
make lab LAB=decouvrir/installation-ansible
make lab LAB=vault/introduction CHALLENGE=1
make lab LAB=vault/introduction BOTH=1
```

### Statuts d'un lab

| Icône | Statut | Signification |
| --- | --- | --- |
| `✅` | `completed` | Au moins un run avec 100 % de tests passed |
| `⏳` | `in_progress` | Run(s) existant(s) avec une partie passed/failed |
| `❌` | `failed` | Tous les tests échouent |
| `·` | `not_started` | Aucun run inscrit |
| `⊘` | `skipped` | Run skippé (challenge non écrit, replay désactivé) |

### Désactiver le suivi

```bash
DSOXLAB_DISABLED=1 pytest …                     # un run sans inscription
DSOXLAB_DB=/tmp/test.db pytest …                # DB alternative (sandbox)
```

### Stockage

- **Local par défaut** : `~/.local/share/dsoxlab/progress.db` (gitignored).
- **Multi-postes** : `bin/dsoxlab export` produit un JSON portable pour
  archiver sa progression ou la fournir à un formateur.
- **Aucun service externe** : pas de réseau, pas d'auth, pas de RGPD.

---

## 🔍 Linter avec `ansible-lint`

`ansible-lint` détecte les anti-patterns dans vos playbooks (FQCN manquant,
modules dépréciés, modes en chaîne, idempotence cassée, etc.). Lancez-le
**systématiquement** avant de commiter ou de lancer pytest :

```bash
# Lint ciblé sur votre solution d'un lab
ansible-lint labs/ecrire-code/block-rescue-always/challenge/solution.yml

# Profil production (le plus strict)
ansible-lint --profile production labs/ecrire-code/block-rescue-always/challenge/solution.yml

# Lint global du dépôt
make lint-all
```

Si `ansible-lint` retourne sans erreur (`Passed: 0 failure(s), 0 warning(s)`),
votre code est conforme aux bonnes pratiques. Vous pouvez aussi utiliser
**`yamllint`** pour la pure syntaxe YAML :

```bash
yamllint labs/ecrire-code/block-rescue-always/challenge/solution.yml
```

---

## 📚 Liste des labs

<!-- LABS_LIST_START -->

**108 labs** répartis en **23 sections** (source de vérité : [`meta.yml`](./meta.yml)).

### Bootstrap

Préparation système des managed nodes (joué auto par `make provision`).

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
- [`parallelisme strategies`](./labs/ecrire-code/parallelisme-strategies/)
- [`async poll`](./labs/ecrire-code/async-poll/)
- [`delegation`](./labs/ecrire-code/delegation/)
- [`variables base`](./labs/ecrire-code/variables-base/)
- [`types collections`](./labs/ecrire-code/types-collections/)
- [`facts magic vars`](./labs/ecrire-code/facts-magic-vars/)
- [`custom facts`](./labs/ecrire-code/custom-facts/)
- [`precedence variables`](./labs/ecrire-code/precedence-variables/)
- [`register set fact`](./labs/ecrire-code/register-set-fact/)
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
- [`selinux`](./labs/modules-rhel/selinux/)
- [`sysctl`](./labs/modules-rhel/sysctl/)
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

- [`group vars host vars`](./labs/inventaires/group-vars-host-vars/)
- [`patterns hotes`](./labs/inventaires/patterns-hotes/)
- [`dynamique kvm`](./labs/inventaires/dynamique-kvm/)

### Rôles

Anatomie d'un rôle, variables, handlers, argument_specs, consommation, dépendances.

- [`creer premier role`](./labs/roles/creer-premier-role/)
- [`variables defaults vars`](./labs/roles/variables-defaults-vars/)
- [`handlers meta`](./labs/roles/handlers-meta/)
- [`argument specs`](./labs/roles/argument-specs/)
- [`consommer role`](./labs/roles/consommer-role/)
- [`dependencies`](./labs/roles/dependencies/)

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
- [`requirements`](./labs/collections/requirements/)
- [`creer custom`](./labs/collections/creer-custom/)
- [`ci tests`](./labs/collections/ci-tests/)
- [`migration role`](./labs/collections/migration-role/)

### Pratiques avancées

ansible-pull mode GitOps.

- [`ansible pull gitops`](./labs/pratiques/ansible-pull-gitops/)

### Examen RHCE EX294

Mock examen complet 4h avec 12 tâches.

- [`mock ex294`](./labs/rhce/mock-ex294/)

<!-- LABS_LIST_END -->

---

## 🔧 Pré-requis poste de travail

### Système supporté

- **Linux** (Fedora, Ubuntu/Debian, Arch, AlmaLinux/Rocky/RHEL).
- **macOS** : possible mais non testé pour la partie libvirt (utilisez WSL2
  ou une VM Linux).
- **Windows** : non supporté directement (utilisez WSL2 + libvirt sous Linux).

### Outils requis

| Outil | Rôle | Installation rapide |
| --- | --- | --- |
| **`pipx`** | Gestionnaire d'apps Python isolées | `sudo dnf install pipx` (Fedora) / `sudo apt install pipx` (Debian) |
| **`ansible`** | Le moteur | `pipx install --include-deps ansible` |
| **`ansible-lint`** | Linter | `pipx install ansible-lint` |
| **`pytest` + `testinfra`** | Tests d'infra | `pipx install pytest && pipx inject pytest pytest-testinfra` |
| **`libvirt` + `qemu-kvm`** | Virtualisation | `make bootstrap` (couvre tout le reste) |

> 💡 **Tout-en-un** : `make bootstrap` à la racine du repo installe **tous**
> les outils ci-dessus. C'est l'option recommandée.

### Vérifier l'installation

```bash
ansible --version          # core 2.18+
ansible-lint --version     # 25+
pytest --version           # 8+
virsh list --all           # libvirt accessible
```

Si une commande manque, relancez `make bootstrap` ou installez-la
manuellement. La page MDX [installation-ansible](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/installation-ansible/)
détaille les 5 méthodes d'installation possibles.

---

## 🆘 Dépannage

### `make verify-conn` échoue (UNREACHABLE)

```bash
# Reset complet du lab
make destroy
make provision
make verify-conn
```

### Un lab marque tous ses tests pytest en `skipped`

C'est attendu : la fixture `_apply_lab_state` skippe avec un message
explicite tant que vous n'avez pas écrit votre `challenge/solution.yml`.

```text
SKIPPED [...] Aucun challenge/solution.yml ni solution.sh trouvé.
L'apprenant doit l'écrire en suivant challenge/README.md, puis relancer pytest.
```

### Un lab échoue parce qu'un lab précédent a polluéle système

Lancez la cible `clean` du lab cible :

```bash
make -C labs/<section>/<lab>/ clean
```

Pour un reset radical, relancez tout le bootstrap :

```bash
make destroy && make provision
```

### `ansible-lint` se plaint de FQCN manquant

Préférez **toujours** `ansible.builtin.copy` à `copy`, `ansible.posix.firewalld`
à `firewalld`, etc. Le FQCN est obligatoire pour la RHCE 2026 et règle
~80 % des warnings d'`ansible-lint`.

### Un challenge ne se déclenche pas avec `--extra-vars` ou `--tags`

Le `conftest.py` racine définit deux mappings (`_PRE_CLEANUPS` et
`_EXTRA_ARGS`) pour gérer les labs qui demandent un setup particulier
(ex : `--tags configuration`, `--extra-vars service_name=…`). Si un test
échoue parce qu'une variable manque ou qu'un fichier annexe pollue l'état,
vérifiez l'entrée correspondante dans [`conftest.py`](./conftest.py).

---

## 🤝 Contribuer

Les retours, corrections et suggestions sont les bienvenus !

1. Créez une **issue** pour signaler un bug ou proposer une amélioration.
2. Forkez le dépôt et ouvrez une **pull request**.

Voir [`contributing.md`](./contributing.md) pour les bonnes pratiques.

---

## ☕ Soutenir le projet

Si ce dépôt vous est utile et que vous voulez soutenir l'auteur :

[![Ko-fi](https://www.ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/votre-identifiant)

---

## © Licence

- **Auteur** : Stéphane Robert (2025-2026)
- **Licence** : [Creative Commons BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

![Creative Commons BY-SA](https://mirrors.creativecommons.org/presskit/buttons/88x31/png/by-sa.png)

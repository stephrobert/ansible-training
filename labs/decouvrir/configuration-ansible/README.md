# Lab 03a — Configuration Ansible (`ansible.cfg`, précédence, options critiques)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `make bootstrap && make provision` à la racine du repo (cf.
> [README racine](../../README.md#-démarrage-rapide) pour les détails).

## 🧠 Rappel

🔗 [**Configuration Ansible : ansible.cfg, précédence, options critiques**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/configuration-ansible/)

Tout projet Ansible mature dispose d'un **`ansible.cfg`** qui fixe les **options par défaut** : chemin de l'inventaire, user SSH, comportement de `become`, callbacks, **forks**, **pipelining**, **roles_path**, **collections_path**. Sans ce fichier, Ansible utilise des **valeurs par défaut globales** rarement adaptées à un projet — et chaque exécution exige des arguments CLI répétitifs.

L'examen RHCE EX294 vous demande de **configurer correctement** un projet Ansible : créer un `ansible.cfg`, comprendre la **précédence** (où est lu en premier), et connaître les **options critiques** qui changent le comportement de runs. Cette page maîtrise ces 3 axes.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Comprendre** la précédence de chargement d'`ansible.cfg` (`ANSIBLE_CONFIG` env > `./ansible.cfg` > `~/.ansible.cfg` > `/etc/ansible/ansible.cfg`).
2. **Créer** un `ansible.cfg` projet avec les options essentielles (`inventory`, `remote_user`, `host_key_checking`, `forks`, `roles_path`, `collections_path`).
3. **Vérifier** la config active avec **`ansible-config dump --only-changed`**.
4. **Surcharger** une option via **variable d'environnement** (`ANSIBLE_FORKS=20`).
5. **Activer** un callback (`ansible.posix.profile_tasks`) sans toucher à un playbook.
6. **Distinguer** options `[defaults]` vs `[ssh_connection]` vs `[privilege_escalation]`.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ansible.builtin.ping
ansible db1.lab -b -m ansible.builtin.file -a "path=/tmp/lab03a-config.txt state=absent" 2>&1 | tail -2
```

## ⚙️ Arborescence cible

```text
labs/decouvrir/configuration-ansible/
├── README.md                       ← ce fichier (tuto guidé)
├── Makefile                        ← cible clean
├── ansible.cfg                     ← (à créer en exo 2)
└── challenge/
    ├── README.md                   ← consigne du challenge
    └── tests/
        └── test_configuration.py   ← tests pytest+testinfra
```

L'apprenant écrit lui-même `ansible.cfg`, `lab.yml` et `challenge/solution.yml`.

## 📚 Exercice 1 — Précédence des fichiers `ansible.cfg`

Ansible cherche son fichier de configuration dans **cet ordre** (1er trouvé gagne) :

| Priorité | Source | Quand l'utiliser |
|----------|--------|------------------|
| 1 (max) | **`$ANSIBLE_CONFIG`** | Pointer vers un fichier custom (CI, test) |
| 2 | **`./ansible.cfg`** dans le répertoire courant | **Recommandé pour un projet** |
| 3 | **`~/.ansible.cfg`** | Préférences utilisateur globales |
| 4 (min) | **`/etc/ansible/ansible.cfg`** | Config système (rare) |

Vérifier quel fichier Ansible utilise actuellement :

```bash
ansible --version | grep "config file"
```

🔍 **Observation** : si vous lancez Ansible depuis un dossier qui contient un `ansible.cfg`, **c'est celui-ci qui est utilisé**. C'est pourquoi un `ansible.cfg` projet à la **racine du repo** est le pattern standard 2026.

## 📚 Exercice 2 — Créer un `ansible.cfg` projet

Créer `labs/decouvrir/configuration-ansible/ansible.cfg` :

```ini
[defaults]
inventory = ../../inventory/hosts.yml
remote_user = ansible
host_key_checking = False
forks = 20
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible-fact-cache
fact_caching_timeout = 7200
stdout_callback = yaml
callbacks_enabled = ansible.posix.profile_tasks, ansible.posix.timer
retry_files_enabled = False
deprecation_warnings = False
roles_path = ./roles:~/.ansible/roles
collections_path = ./collections:~/.ansible/collections

[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = False

[ssh_connection]
pipelining = True
ssh_args = -C -o ControlMaster=auto -o ControlPersist=60s
```

Vérifier que ce fichier est bien lu :

```bash
cd labs/decouvrir/configuration-ansible/
ansible --version | grep "config file"
# → config file = /home/bob/Projets/ansible-training/labs/03a-.../ansible.cfg
```

🔍 **Observation** : 3 sections principales — **`[defaults]`** (comportement général), **`[privilege_escalation]`** (sudo/become), **`[ssh_connection]`** (transport SSH). Chaque option a une **variable d'env équivalente** : `ANSIBLE_FORKS`, `ANSIBLE_HOST_KEY_CHECKING`, etc.

## 📚 Exercice 3 — Inspecter la config active

```bash
ansible-config dump --only-changed
```

Sortie typique :

```text
DEFAULT_FORKS(/home/.../ansible.cfg) = 20
DEFAULT_GATHERING(/home/.../ansible.cfg) = smart
DEFAULT_HOST_LIST(/home/.../ansible.cfg) = ['/home/.../inventory/hosts.yml']
DEFAULT_REMOTE_USER(/home/.../ansible.cfg) = ansible
DEFAULT_STDOUT_CALLBACK(/home/.../ansible.cfg) = yaml
HOST_KEY_CHECKING(/home/.../ansible.cfg) = False
```

🔍 **Observation cruciale** : **`--only-changed`** affiche **uniquement** les options qui diffèrent du défaut. **Référence** pour vérifier ce que votre `ansible.cfg` modifie réellement. À utiliser en debug (« pourquoi ce comportement ? » → vérifier la config active).

## 📚 Exercice 4 — Surcharger une option via variable d'env

```bash
# Sans surcharge : forks = 20 (défini dans ansible.cfg)
ansible-config dump --only-changed | grep FORKS

# Avec surcharge : forks = 50 pour cette commande
ANSIBLE_FORKS=50 ansible-config dump --only-changed | grep FORKS
# → DEFAULT_FORKS(env: ANSIBLE_FORKS) = 50
```

🔍 **Observation** : la **variable d'env** a une **précédence supérieure** au fichier `ansible.cfg`. Pratique pour **surcharger ponctuellement** sans modifier le fichier (CI, debug, test ad-hoc). La sortie de `ansible-config dump` montre la **source** entre parenthèses (`env:` ou `path:`).

## 📚 Exercice 5 — Activer un callback (`profile_tasks`)

Créer un `lab.yml` simple :

```yaml
---
- hosts: db1.lab
  gather_facts: false
  tasks:
    - ansible.builtin.shell: sleep 1
      changed_when: false
    - ansible.builtin.shell: sleep 0.5
      changed_when: false
    - ansible.builtin.ping:
```

Lancer (avec `ansible.cfg` qui active `profile_tasks`) :

```bash
ansible-playbook lab.yml
```

Sortie en fin de run :

```text
TASK execution time:
   1.    sleep 1 ───────────────── 1.05s
   2.    sleep 0.5 ────────────── 0.52s
   3.    ping ─────────────────── 0.12s

Playbook run took 0 days, 0 hours, 0 minutes, 2 seconds
```

🔍 **Observation** : pas besoin de modifier le playbook pour mesurer les performances. **`callbacks_enabled = ansible.posix.profile_tasks`** dans `ansible.cfg` suffit. Pattern indispensable pour identifier les **goulots** sur une fleet de production.

## 📚 Exercice 6 — `roles_path` et `collections_path`

Créer un rôle local :

```bash
mkdir -p roles/check_disk/tasks
cat > roles/check_disk/tasks/main.yml <<'EOF'
---
- ansible.builtin.shell: df -h /
  register: disk
  changed_when: false
- ansible.builtin.debug:
    var: disk.stdout_lines
EOF
```

Avec `roles_path = ./roles:~/.ansible/roles` dans `ansible.cfg` :

```yaml
- hosts: db1.lab
  gather_facts: false
  roles:
    - check_disk
```

Lancer : Ansible **trouve** le rôle dans `./roles/` grâce au `roles_path`.

🔍 **Observation** : sans `roles_path` configuré, Ansible cherche **uniquement** dans `~/.ansible/roles/` et `/usr/share/ansible/roles/`. Ajouter `./roles:` rend les rôles **locaux au projet** prioritaires — pattern standard en 2026.

## 📚 Exercice 7 — Précédence env > cfg démontrée

```bash
# Forks à 20 dans ansible.cfg, à 50 via env
ANSIBLE_FORKS=50 ansible-playbook lab.yml -v 2>&1 | head -3
```

Vérifier le forks effectivement utilisé via `ansible-config dump`.

🔍 **Observation** : la **chaîne de précédence** est : variables d'env → `ansible.cfg` projet → `~/.ansible.cfg` → `/etc/ansible/ansible.cfg` → défaut. **Toujours dans cet ordre**. Permet de **surcharger** finement (env en CI, fichier projet en team, fichier user en perso).

## 🔍 Observations à noter

- **Précédence** : `ANSIBLE_CONFIG` env > `./ansible.cfg` > `~/.ansible.cfg` > `/etc/ansible/ansible.cfg`.
- **3 sections principales** : `[defaults]`, `[privilege_escalation]`, `[ssh_connection]`.
- **`ansible-config dump --only-changed`** = inspection de la config effective.
- **Variables d'env** : `ANSIBLE_FORKS`, `ANSIBLE_HOST_KEY_CHECKING`, etc. surchargent le fichier.
- **Callbacks** activés via `callbacks_enabled = ansible.posix.profile_tasks, ...`.
- **`roles_path` / `collections_path`** rendent les ressources **locales au projet** prioritaires.

## 🤔 Questions de réflexion

1. Que se passe-t-il si **deux** `ansible.cfg` existent : un dans `./` et un dans `~/.ansible.cfg` ?
2. Pourquoi `host_key_checking = False` est-il **acceptable en lab** mais **dangereux en prod** ?
3. Quelle option `[ssh_connection]` est **incompatible** avec `Defaults requiretty` dans `/etc/sudoers` ?
4. Comment **désactiver** un callback temporairement sans modifier `ansible.cfg` ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) — créer un `ansible.cfg` qui active `profile_tasks`, force `forks=20`, et déposer un fichier preuve qui contient le résultat de `ansible-config dump --only-changed`.

## 💡 Pour aller plus loin

- **Lab 91** : tuning performances avancé (pipelining, ControlPersist).
- **`ansible-config view`** : affiche l'`ansible.cfg` effectif avec commentaires.
- **`ansible-config init --disabled > ansible.cfg`** : génère un fichier de config vide avec **toutes** les options documentées.
- **Variables d'env exhaustives** : voir `ansible-config list` pour la liste complète.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/decouvrir/configuration-ansible/lab.yml
ansible-lint --profile production labs/decouvrir/configuration-ansible/challenge/solution.yml
```

> 💡 **Astuce** : `ansible-lint` ne vérifie pas le contenu d'`ansible.cfg`. Pour valider la **syntaxe** : `ansible-config view` retourne une erreur si le fichier est mal formé.

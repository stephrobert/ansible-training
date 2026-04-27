# Lab 89 — Verbosité progressive (`-v` à `-vvvv`) et callback plugins

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

🔗 [**Verbosité Ansible : -v / -vv / -vvv / -vvvv**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/verbosite-vvv/)

Quand un playbook échoue, **les flags de verbosité** sont vos premiers outils. Chaque niveau ouvre un nouveau cran d'information :

| Flag | Apporte |
| --- | --- |
| `-v` | Résultats des tâches enrichis |
| `-vv` | Arguments réels passés au module (post-template Jinja2) |
| `-vvv` | Détails connexion SSH, chemin tmp module sur la cible |
| `-vvvv` | Internals plugin de connexion, scp/sftp raw, ControlMaster |

En complément, les **callback plugins** comme `ansible.posix.profile_tasks` mesurent le **temps par tâche** sans toucher au code du playbook. Maîtriser ces deux leviers résout 80 % des erreurs de production.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Choisir** le bon niveau `-v` selon le symptôme (variable Jinja vs SSH vs autre).
2. **Activer** un callback `profile_tasks` via `ansible.cfg` pour mesurer les performances.
3. **Distinguer** les arguments **post-template** (`-vv`) des connexions SSH (`-vvv`).
4. **Activer** `stdout_callback = yaml` pour des sorties multi-ligne lisibles.
5. **Sortir un secret** par mégarde **et** comprendre pourquoi `no_log: true` est obligatoire.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ansible.builtin.ping
ansible db1.lab -b -m ansible.builtin.file -a "path=/tmp/lab89-* state=absent" 2>&1 | tail -2
```

## ⚙️ Arborescence cible

```text
labs/troubleshooting/verbosite/
├── README.md                       ← ce fichier (tuto guidé)
├── Makefile                        ← cible clean
├── ansible.cfg                     ← (à créer en exercice 4)
└── challenge/
    ├── README.md                   ← consigne challenge avec squelette
    └── tests/
        └── test_verbosite.py       ← tests pytest+testinfra
```

L'apprenant écrit lui-même `lab.yml` (au fil des exercices) et `challenge/solution.yml`.

## 📚 Exercice 1 — Provoquer une erreur Jinja2 et l'observer en `-v`

Créez un `lab.yml` avec une **variable mal nommée** :

```yaml
---
- name: Lab 89 — debug verbosité
  hosts: db1.lab
  gather_facts: false
  vars:
    db_user: "appuser"
  tasks:
    - name: Erreur volontaire — variable inexistante
      ansible.builtin.debug:
        msg: "User: {{ db_use }}"     # ← typo volontaire (db_use au lieu de db_user)
```

Lancer en mode normal :

```bash
ansible-playbook labs/troubleshooting/verbosite/lab.yml
```

Sortie typique :

```text
fatal: [db1.lab]: FAILED! => {"msg": "The task includes an option with an undefined variable. The error was: 'db_use' is undefined..."}
```

🔍 **Observation** : sans `-v`, le message dit **où** ça plante mais **pas** ce que la variable contenait avant le template. Insuffisant pour des cas Jinja2 plus complexes.

## 📚 Exercice 2 — Voir les variables résolues avec `-vv`

```bash
ansible-playbook labs/troubleshooting/verbosite/lab.yml -vv
```

Sortie complémentaire :

```text
task path: /home/bob/Projets/ansible-training/labs/89-…/lab.yml:7
The error appears to be in '…': line 7, column 7
…
TASK [Erreur volontaire — variable inexistante] ***
fatal: [db1.lab]: FAILED! => {"msg": "...db_use is undefined..."}
```

🔍 **Observation** : `-vv` ajoute le **chemin du fichier:ligne** et les **arguments réels** passés à chaque module. C'est le niveau **par défaut quotidien** quand on développe un playbook.

## 📚 Exercice 3 — Diagnostiquer un échec SSH avec `-vvv`

Modifier `lab.yml` pour cibler un host inexistant :

```yaml
- name: Échec SSH volontaire
  hosts: nonexistent.lab
  gather_facts: false
  tasks:
    - ansible.builtin.ping:
```

Lancer :

```bash
ansible-playbook labs/troubleshooting/verbosite/lab.yml -vvv
```

Sortie typique :

```text
ESTABLISH SSH CONNECTION FOR USER: ansible
SSH: EXEC ssh -C -o ControlMaster=auto -o ControlPersist=60s …
ssh: Could not resolve hostname nonexistent.lab: Name or service not known
```

🔍 **Observation** : `-vvv` montre la **commande SSH exacte** qu'Ansible exécute. Reproduisez-la à la main avec `ssh -vvv user@host` pour bypass complètement Ansible. C'est le niveau **incontournable** pour diagnostiquer du réseau.

## 📚 Exercice 4 — Activer le callback `profile_tasks`

Créer `ansible.cfg` à la racine du lab :

```ini
[defaults]
stdout_callback = yaml
callbacks_enabled = ansible.posix.profile_tasks, ansible.posix.timer

[callback_profile_tasks]
task_output_limit = 10
```

Avec un playbook qui fait plusieurs tâches :

```yaml
---
- hosts: db1.lab
  gather_facts: false
  tasks:
    - ansible.builtin.shell: sleep 2
      changed_when: false
    - ansible.builtin.shell: sleep 1
      changed_when: false
    - ansible.builtin.ping:
```

Lancer :

```bash
ANSIBLE_CONFIG=labs/troubleshooting/verbosite/ansible.cfg \
  ansible-playbook labs/troubleshooting/verbosite/lab.yml
```

Sortie en fin de run :

```text
TASK execution time:
   1.    sleep 2 ──────────────── 2.05s
   2.    sleep 1 ──────────────── 1.04s
   3.    ping ──────────────────── 0.82s
Playbook run took 0 days, 0 hours, 0 minutes, 4 seconds
```

🔍 **Observation** : `profile_tasks` trie les tâches par durée descendante. **Indispensable** pour identifier le top des tâches lentes sur une fleet de production. Le callback `timer` ajoute le **temps total** du playbook.

## 📚 Exercice 5 — `stdout_callback = yaml` pour sortie lisible

Sans le callback `yaml`, une `set_fact` complexe affiche :

```text
ok: [db1.lab] => {"ansible_facts": {"my_data": [{"name": "alice", "age": 30}, {"name": "bob", "age": 25}]}}
```

Avec `stdout_callback = yaml` :

```yaml
ok: [db1.lab] => 
  ansible_facts:
    my_data:
      - name: alice
        age: 30
      - name: bob
        age: 25
```

🔍 **Observation** : sortie **multi-ligne**, lisible humainement, idéal pour debug. À activer par défaut dans `ansible.cfg`.

## 📚 Exercice 6 — Le piège `-v` qui leak un secret

Avec ce playbook (sans `no_log:`) :

```yaml
- ansible.builtin.shell: 'echo "Secret token: super_secret_token_42"'
  register: out
- debug: var=out.stdout
```

Lancer en `-v` :

```bash
ansible-playbook lab.yml -v
```

Sortie :

```text
ok: [db1.lab] =>
  out.stdout: "Secret token: super_secret_token_42"
```

🔍 **Observation cruciale** : **`-v` peut révéler des secrets** dans la sortie. **Toujours** ajouter **`no_log: true`** sur les tâches qui manipulent des credentials :

```yaml
- ansible.builtin.shell: 'echo "Secret token: super_secret_token_42"'
  register: out
  no_log: true                  # ← bloque la sortie en -v
```

## 🔍 Observations à noter

- **`-v`** = niveau quotidien dev pour voir résultats détaillés.
- **`-vv`** = chemin fichier + args templatés. Bug Jinja2 → utiliser `-vv`.
- **`-vvv`** = commande SSH exacte. Bug réseau / connexion → utiliser `-vvv`.
- **`-vvvv`** = internals plugin de connexion. Très rare, surtout pour ControlMaster.
- **Callbacks** : `profile_tasks` + `timer` + `stdout_callback=yaml` dans `ansible.cfg`.
- **`no_log: true`** systématique sur toute tâche manipulant un secret.

## 🤔 Questions de réflexion

1. À quel niveau de verbosité voit-on les **arguments substitués Jinja2** ?
2. Pourquoi `-vvvv` est-il rarement utile en production ?
3. Que se passe-t-il si `no_log: true` est posé sur le **module** au lieu de la **task** ?
4. Comment **désactiver les couleurs** dans la sortie pour un log CI ? (Indice : `ANSIBLE_FORCE_COLOR=0` ou `--no-color`).

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) — créer un playbook avec **3 tâches mesurées** par `profile_tasks` qui dépose un fichier de timing sur `db1.lab`.

## 💡 Pour aller plus loin

- **Lab 90** : débogueur interactif `(debug)` REPL.
- **Lab 91** : idempotence cassée + tuning forks/pipelining.
- **Variable `ANSIBLE_DEBUG=1`** : debug du moteur Ansible (très verbeux).
- **`ANSIBLE_KEEP_REMOTE_FILES=1`** : conserve les modules sur la cible pour inspection (lab 91).

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/troubleshooting/verbosite/lab.yml
ansible-lint labs/troubleshooting/verbosite/challenge/solution.yml
ansible-lint --profile production labs/troubleshooting/verbosite/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques.

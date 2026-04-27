# Lab 90 — Débogueur Ansible interactif (`debugger: on_failed`)

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

🔗 [**Débogueur Ansible interactif**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/debugger-interactif/)

Quand une tâche échoue dans un playbook long, **relancer tout depuis le début** est lent et frustrant. Ansible fournit un **débogueur interactif** qui ouvre un **REPL** au moment de l'échec : on inspecte les variables, on **modifie les arguments à chaud** (`task.args['name'] = 'nginx'`), on **rejoue** la tâche modifiée (`redo`), on **continue** le playbook (`continue`).

Activable au niveau task ou play avec `debugger: on_failed`. **Indispensable** pour itérer rapidement sur un bug sans relancer 100 tâches.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Activer** le débogueur via `debugger: on_failed` au niveau play/task.
2. **Inspecter** les variables (`p task`, `p task.args`, `p task_vars['x']`, `p result`).
3. **Modifier** les args d'une tâche à chaud (`task.args['name'] = 'httpd'`).
4. **Rejouer** la tâche modifiée (`redo`).
5. **Continuer** le playbook (`continue`) ou abandonner (`quit`).
6. Comprendre **quand** le débogueur n'est PAS pertinent (CI, productions automatisées).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ansible.builtin.ping
ansible db1.lab -b -m ansible.builtin.file -a "path=/tmp/lab90-debug.txt state=absent" 2>&1 | tail -2
```

## ⚙️ Arborescence cible

```text
labs/troubleshooting/debugger/
├── README.md                       ← tuto guidé
├── Makefile                        ← cible clean
└── challenge/
    ├── README.md                   ← consigne challenge
    └── tests/
        └── test_debugger.py        ← tests pytest+testinfra
```

L'apprenant écrit lui-même `lab.yml` (au fil des exercices) et `challenge/solution.yml`.

## 📚 Exercice 1 — Activer `debugger: on_failed`

Créer `lab.yml` qui **échoue volontairement** (paquet inexistant) :

```yaml
---
- name: Lab 90 — débogueur interactif
  hosts: db1.lab
  become: true
  gather_facts: false
  debugger: on_failed                # ← active le REPL en cas d'échec
  tasks:
    - name: Installer un paquet inexistant
      ansible.builtin.dnf:
        name: nginx-impossible-2026  # ← n'existe pas
        state: present
```

Lancer :

```bash
ansible-playbook labs/troubleshooting/debugger/lab.yml
```

Sortie typique :

```text
TASK [Installer un paquet inexistant] ***
fatal: [db1.lab]: FAILED! => {"msg": "...nginx-impossible-2026..."}

[db1.lab] TASK: Installer un paquet inexistant (debug)>
```

🔍 **Observation** : le prompt **`(debug)>`** indique que vous êtes dans le REPL. La tâche n'a pas relancé tout le play, elle s'est arrêtée **précisément** sur l'échec. Tapez `help` pour la liste des commandes.

## 📚 Exercice 2 — Inspecter les variables au runtime

Au prompt `(debug)>` :

```text
(debug)> p task
TASK: Installer un paquet inexistant
(debug)> p task.args
{'name': 'nginx-impossible-2026', 'state': 'present'}
(debug)> p task_vars['inventory_hostname']
'db1.lab'
(debug)> p result._result
{'failed': True, 'msg': '...nginx-impossible-2026...', ...}
```

🔍 **Observation** : `p` (print) accepte n'importe quelle expression Python. `task_vars` contient **toutes** les variables résolues pour le host (group_vars, host_vars, facts, vars du play). Permet de répondre à « quelle valeur la variable a-t-elle au moment de l'échec ? ».

## 📚 Exercice 3 — Modifier les args à chaud + redo

Toujours au prompt `(debug)>` :

```text
(debug)> task.args['name'] = 'nginx'
(debug)> redo
ok: [db1.lab]
[db1.lab] TASK: Tâche suivante (debug)>
```

🔍 **Observation** : on a **modifié** la tâche au runtime, **rejoué**, et la tâche est passée. **Pas besoin de relancer le playbook** ni d'éditer le YAML. Pour une fleet de 50 hôtes où une seule tâche plante, c'est inestimable. **`continue`** fait passer à la tâche suivante, **`quit`** abandonne.

## 📚 Exercice 4 — `task_vars` modifiable

Si l'erreur vient d'une variable :

```yaml
- ansible.builtin.copy:
    dest: /tmp/lab90-debug.txt
    content: "Hello {{ undef_var }}"
    mode: "0644"
```

Au prompt `(debug)>` :

```text
(debug)> task_vars['undef_var'] = 'world'
(debug)> update_task
(debug)> redo
ok: [db1.lab]
```

🔍 **Observation** : `task_vars['x'] = 'y'` injecte la variable, **`update_task`** (raccourci `u`) recrée la tâche avec les nouveaux vars, puis `redo` rejoue. Workflow puissant pour résoudre des `undefined variable`.

## 📚 Exercice 5 — Stratégie `linear` vs `free` en debug

```yaml
- hosts: webservers
  strategy: free       # ← tâches indépendantes par host
  debugger: on_failed
```

🔍 **Observation cruciale** : avec **`strategy: free`**, pendant que vous êtes au prompt `(debug)>` sur web1.lab, **les tâches de web2.lab continuent à tourner**. Préférer **`strategy: linear`** (default) en debug — pause synchrone sur tous les hosts.

## 📚 Exercice 6 — Quand NE PAS utiliser le débogueur

Le débogueur est **interactif**. À ne pas activer :

- En **CI/CD** : aucun stdin, le pipeline freeze indéfiniment.
- Sur **AWX / AAP** : les jobs n'ont pas de prompt utilisateur.
- En cron / systemd timer : pareil.

Pour ces contextes, préférer :

- **`ANSIBLE_KEEP_REMOTE_FILES=1`** + **artefacts `ansible-navigator`** (lab 91 + EE).
- **Logs détaillés** avec **`-vv` ou `-vvv`** (lab 89).
- **Tests** Molecule sur des scénarios reproductibles (labs roles 62-65).

## 🔍 Observations à noter

- **`debugger: on_failed`** au niveau play ou task — pas global.
- **`p`** print, accepte n'importe quelle expression Python.
- **`task.args['x'] = ...`** + **`redo`** modifie + rejoue.
- **`task_vars['x'] = ...`** + **`update_task`** (`u`) + **`redo`** modifie une variable.
- **`strategy: linear`** mandatory en debug (sinon free crée des races).
- **Pas de débogueur en CI** — interactivité requise.

## 🤔 Questions de réflexion

1. Quelles autres valeurs prend `debugger:` ? (Indice : `always`, `never`, `on_failed`, `on_unreachable`, `on_skipped`).
2. Comment activer le débogueur **globalement** sans le mettre dans le YAML ? (Indice : `ANSIBLE_ENABLE_TASK_DEBUGGER=True`).
3. Pourquoi `strategy: free` est-il **dangereux** avec un débogueur ?
4. Le débogueur ouvre-t-il un prompt sur **chaque host** qui échoue, ou un seul ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) — utiliser le débogueur pour **fix une variable manquante** au runtime et déposer un fichier sur `db1.lab`.

## 💡 Pour aller plus loin

- **`debugger: always`** : ouvre le REPL **après chaque tâche** (lent mais utile en TDD).
- **`ANSIBLE_DISPLAY_TRACEBACK`** (2.18+) : trace Python complète sur exception.
- **Lab 91** : idempotence cassée + tuning.
- **AAP** : pas de débogueur, mais artefacts JSON `ansible-navigator replay`.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/troubleshooting/debugger/lab.yml
ansible-lint labs/troubleshooting/debugger/challenge/solution.yml
ansible-lint --profile production labs/troubleshooting/debugger/challenge/solution.yml
```

> ⚠️ **Note** : `debugger:` n'est pas signalé par ansible-lint mais reste un
> outil de **dev/debug**, jamais à laisser en prod ou CI/CD.

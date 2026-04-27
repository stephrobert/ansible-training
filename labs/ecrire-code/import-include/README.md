# Lab 30a — Import vs Include (`import_tasks`, `include_tasks`, `import_role`, `include_role`, `import_playbook`)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `make bootstrap && make provision` à la racine du repo.

## 🧠 Rappel

🔗 [**Import vs Include : les 5 directives Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/import-include/)

Ansible offre **5 directives** pour découper un playbook en fichiers réutilisables :

- **`import_tasks`** / **`include_tasks`** — inclure un fichier de tâches.
- **`import_role`** / **`include_role`** — inclure un rôle.
- **`import_playbook`** — inclure un autre playbook (au niveau plays).

La distinction **`import_*` (static) vs `include_*` (dynamic)** est **fondamentale** et **testée à l'EX294** : elles n'ont **pas le même comportement** vis-à-vis des **tags**, **conditions**, **variables runtime**, **handlers**, et **`--list-tasks`**. Confondre les deux casse silencieusement vos playbooks.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Distinguer** `import_*` (static, parsé au start) vs `include_*` (dynamic, parsé au runtime).
2. **Choisir** la bonne directive selon le cas (boucle ? conditionnel ? variables runtime ?).
3. **Découper** un playbook avec `import_tasks` pour la lisibilité.
4. **Appeler** un rôle dynamiquement avec `include_role` (utile pour `loop:`).
5. **Orchestrer** plusieurs plays avec `import_playbook`.
6. **Comprendre** comment `tags:` et `when:` se comportent différemment selon import vs include.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ansible.builtin.ping
ansible db1.lab -b -m ansible.builtin.shell -a "rm -f /tmp/lab30a-*" 2>&1 | tail -2
```

## ⚙️ Arborescence cible

```text
labs/ecrire-code/import-include/
├── README.md                       ← ce fichier (tuto guidé)
├── Makefile                        ← cible clean
└── challenge/
    ├── README.md                   ← consigne du challenge
    └── tests/
        └── test_import_include.py
```

L'apprenant écrit lui-même `lab.yml` + les fichiers `tasks/*.yml` + `challenge/solution.yml`.

## 📚 Exercice 1 — `import_tasks` static vs `include_tasks` dynamic

Créer 2 fichiers de tâches :

`tasks/install.yml` :

```yaml
---
- name: Marker install
  ansible.builtin.copy:
    dest: "{{ marker_path }}"
    content: "step: install\n"
    mode: "0644"
```

`tasks/configure.yml` :

```yaml
---
- name: Marker configure
  ansible.builtin.copy:
    dest: "{{ marker_path }}"
    content: "step: configure\n"
    mode: "0644"
```

Dans `lab.yml` :

```yaml
---
- hosts: db1.lab
  become: true
  gather_facts: false
  vars:
    marker_path: /tmp/lab30a-marker.txt
  tasks:
    - name: Static — import_tasks (parsé au start)
      ansible.builtin.import_tasks: tasks/install.yml

    - name: Dynamic — include_tasks (parsé au runtime)
      ansible.builtin.include_tasks: tasks/configure.yml
```

🔍 **Observation** : à l'œil, **rien ne distingue** les 2 directives à l'exécution. Mais ce qui change est **interne** : `import_*` est **résolu au démarrage** (avant exécution), `include_*` au **runtime** (au moment où la tâche est rencontrée).

## 📚 Exercice 2 — Différence VRAIE : variables runtime

Cas où la différence saute aux yeux : **variable définie au runtime** dans une boucle.

```yaml
- hosts: db1.lab
  gather_facts: false
  tasks:
    - name: Include dynamic dans une loop (FONCTIONNE)
      ansible.builtin.include_tasks: tasks/install.yml
      vars:
        marker_path: "/tmp/lab30a-loop-{{ item }}.txt"
      loop: [1, 2, 3]

    # - name: Import static dans une loop (NE FONCTIONNE PAS)
    #   ansible.builtin.import_tasks: tasks/install.yml   ← boucle KO
    #   vars:
    #     marker_path: "..."
    #   loop: [1, 2, 3]
```

🔍 **Observation cruciale** : `import_*` **n'accepte pas `loop:`** car résolu au démarrage (la variable de boucle n'existe pas encore). `include_*` accepte `loop:`. **Règle** : pour boucler sur un fichier de tâches, c'est **`include_tasks`**.

## 📚 Exercice 3 — Différence sur `tags:`

```yaml
- hosts: db1.lab
  tasks:
    - name: Import static — les tags se PROPAGENT aux tâches incluses
      ansible.builtin.import_tasks: tasks/install.yml
      tags: [setup]

    - name: Include dynamic — les tags ne se propagent PAS
      ansible.builtin.include_tasks: tasks/configure.yml
      tags: [setup]
```

Lancer avec `--tags setup` :

```bash
ansible-playbook lab.yml --tags setup
```

🔍 **Observation** :
- `import_tasks` propage **`setup`** à **toutes** les tâches du fichier importé. `--tags setup` les exécute.
- `include_tasks` **n'applique pas le tag** aux tâches **internes** au fichier inclus. Pour qu'elles soient taggées, il faut taguer **chaque tâche** dans `configure.yml`. Source de bug fréquent.

## 📚 Exercice 4 — Différence sur `when:` conditionnel

```yaml
- hosts: db1.lab
  tasks:
    - name: Import — when s'applique à TOUTES les tâches importées
      ansible.builtin.import_tasks: tasks/install.yml
      when: inventory_hostname == "db1.lab"

    - name: Include — when s'évalue UNE FOIS sur le include lui-même
      ansible.builtin.include_tasks: tasks/configure.yml
      when: inventory_hostname == "db1.lab"
```

🔍 **Observation** : sémantique **subtilement différente**. `import_*` propage le `when:` à chaque tâche → évaluation par tâche. `include_*` évalue le `when:` **une seule fois** au moment du include (avant d'exécuter le contenu).

## 📚 Exercice 5 — `import_role` vs `include_role`

```yaml
- hosts: db1.lab
  tasks:
    - name: Import role static (équivalent au mot-clé `roles:` du play)
      ansible.builtin.import_role:
        name: my_role

    - name: Include role dynamic (utilisable dans une loop, conditionnel runtime)
      ansible.builtin.include_role:
        name: my_role
      loop: [1, 2, 3]                       # ← boucle OK avec include_role
```

🔍 **Observation** : `import_role` ≈ `roles:` du play classique. `include_role` permet de **boucler sur un rôle** ou d'appliquer un rôle **conditionnellement au runtime** — usage rare mais puissant pour des patterns dynamiques.

## 📚 Exercice 6 — `import_playbook` pour orchestrer

Un seul fichier d'orchestration `site.yml` qui chaîne plusieurs playbooks :

```yaml
---
# site.yml — orchestrateur
- ansible.builtin.import_playbook: playbooks/install_db.yml
- ansible.builtin.import_playbook: playbooks/install_web.yml
- ansible.builtin.import_playbook: playbooks/configure_app.yml
```

🔍 **Observation** : **`import_playbook`** est **uniquement static** (pas de `include_playbook`). À utiliser au **niveau plays** (pas dans `tasks:`). Pattern standard pour découper un gros déploiement en sous-playbooks réutilisables.

## 📚 Exercice 7 — Tableau de décision

| Cas d'usage | Directive |
|-------------|-----------|
| Découper un playbook en fichiers `tasks/*.yml` (pas de loop) | **`import_tasks`** (static, plus rapide, supporte `--list-tasks`) |
| Boucler sur un fichier de tâches (`loop: [...]`) | **`include_tasks`** (only) |
| Tagger un bloc entier de tâches incluses | **`import_tasks` + `tags:`** (propage automatiquement) |
| Appeler un rôle classiquement | **`import_role`** ou directive `roles:` du play |
| Boucler sur un rôle | **`include_role`** + `loop:` |
| Orchestrer plusieurs plays | **`import_playbook`** (only) |
| Variable de runtime pas encore connue au start | **`include_*`** (any) |

## 🔍 Observations à noter

- **`import_*`** = **static**, parsé au démarrage. Plus rapide. Tags + when propagés.
- **`include_*`** = **dynamic**, parsé au runtime. Supporte `loop:`. Tags + when **non propagés**.
- **`import_playbook`** existe, **`include_playbook` n'existe PAS**.
- **Boucle sur tâches/rôles** → **`include_*`** obligatoire.
- **`--list-tasks`** ne voit que les tâches **importées** (static), pas les incluses (dynamic).

## 🤔 Questions de réflexion

1. Pourquoi `import_*` est-il **plus rapide au start** que `include_*` ?
2. Que retourne `ansible-playbook --list-tasks` pour un `include_tasks` ?
3. Si vous taguez `import_tasks: ... tags: [setup]`, faut-il aussi tagger les tâches **dans** le fichier importé ?
4. Quelle directive choisir pour **importer un playbook entier** : `import_playbook` ou `include_playbook` ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) — combiner `import_tasks` (avec tag) + `include_tasks` (avec loop) + `import_playbook` (orchestrateur).

## 💡 Pour aller plus loin

- **Lab 11** : `delegate_to`, qui peut s'utiliser au niveau task ou block.
- **Lab 23** : `block/rescue/always`, alternative pour grouper des tâches.
- **`apply:`** sur `include_tasks` : applique des tags / become / when à toutes les tâches **internes**. Exemple : `include_tasks: ... apply: { tags: [setup] }`.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/ecrire-code/import-include/lab.yml
ansible-lint --profile production labs/ecrire-code/import-include/challenge/solution.yml
```

> 💡 **Astuce** : `ansible-lint` détecte le module **non-FQCN** (`include_tasks:` au lieu de `ansible.builtin.include_tasks:`) avec la règle `fqcn-builtins`. Toujours utiliser le FQCN complet.

# Lab 56 — Patterns d'hôtes (`web*`, `&prod`, `:`, `!`)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```

## 🧠 Rappel

🔗 [**Patterns d'hôtes Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/patterns-hotes/)

**`--limit`** et les opérateurs de pattern permettent de cibler **précisément** les hôtes voulus sans toucher au playbook. Quatre opérateurs essentiels :

| Opérateur | Effet | Exemple |
|---|---|---|
| **`:`** | Union (OU logique) | `webservers:dbservers` = web1 + web2 + db1 |
| **`:&`** | Intersection (ET logique) | `webservers:&staging` = web1 (présent dans les 2) |
| **`:!`** | Exclusion | `webservers:!web1.lab` = web2 |
| **`*`** | Wildcard | `web*.lab` = web1.lab + web2.lab |

À l'examen RHCE, savoir cibler avec précision est **mandatory** pour ne pas exécuter une tâche dangereuse sur le mauvais host.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Lister les hôtes ciblés par un pattern via **`--list-hosts`** (sans rien exécuter).
2. Combiner **union**, **intersection**, **exclusion** dans un même pattern.
3. Utiliser des **wildcards** (`*`) pour matcher des noms.
4. Appliquer **`--limit`** sur un playbook pour réduire la portée.
5. Comprendre l'**ordre de priorité** des opérateurs.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training/labs/inventaires/patterns-hotes
ansible-inventory -i inventory/hosts.yml --graph
```

L'inventaire de ce lab a **6 groupes** : `webservers`, `dbservers`, `prod` (parent), `staging`, `monitoring`, plus le `@ungrouped` automatique. Certains hôtes appartiennent à **plusieurs groupes** — c'est ça qui rend les intersections intéressantes.

## ⚙️ Arborescence cible

```text
labs/inventaires/patterns-hotes/
├── README.md           ← ce fichier
├── inventory/
│   └── hosts.yml       ← inventaire avec hôtes multi-groupes
└── challenge/
    ├── README.md
    ├── solution.yml    ← playbook qui pose un marqueur sur chaque host
    └── tests/
        └── test_patterns.py
```

## 📚 Exercice 1 — Découvrir l'inventaire

```bash
ansible-inventory -i inventory/hosts.yml --graph
```

Notez l'appartenance multiple : **`web1.lab`** est dans `webservers`, `prod` (via children), et `staging`. **`db1.lab`** est dans `dbservers`, `prod`, et `monitoring`.

🔍 **Observation** : Ansible permet à un host d'être dans **autant de groupes** que vous voulez. C'est ce qui rend les intersections puissantes.

## 📚 Exercice 2 — Pattern `all`

```bash
ansible all -i inventory/hosts.yml --list-hosts
```

Sortie : `web1.lab`, `web2.lab`, `db1.lab`. **`all`** est le groupe racine implicite.

## 📚 Exercice 3 — Union avec `:`

```bash
ansible 'webservers:dbservers' -i inventory/hosts.yml --list-hosts
```

Sortie : `web1.lab`, `web2.lab`, `db1.lab`. L'**union** retourne tous les hôtes des deux groupes.

🔍 **Observation** : les **quotes simples** sont **mandatory** autour du pattern — sans elles, le shell interprète le `:` comme un séparateur de fichier ou autre.

## 📚 Exercice 4 — Intersection avec `:&`

```bash
ansible 'webservers:&staging' -i inventory/hosts.yml --list-hosts
```

Sortie : **`web1.lab`** uniquement. **L'intersection** retourne les hôtes présents **dans les deux** groupes. `web1.lab` est dans `webservers` ET dans `staging`. `web2.lab` est dans `webservers` mais **pas** dans `staging` → exclu.

🔍 **Observation** : pattern précieux pour des actions **chirurgicales** — par exemple, déployer un patch uniquement sur les machines qui sont **à la fois** webservers ET en staging.

## 📚 Exercice 5 — Exclusion avec `:!`

```bash
ansible 'webservers:!web1.lab' -i inventory/hosts.yml --list-hosts
```

Sortie : **`web2.lab`** uniquement. **`!web1.lab`** retire `web1.lab` du groupe.

```bash
ansible 'all:!dbservers' -i inventory/hosts.yml --list-hosts
```

Sortie : `web1.lab`, `web2.lab`. Tous **sauf** les dbservers.

## 📚 Exercice 6 — Wildcards

```bash
ansible 'web*.lab' -i inventory/hosts.yml --list-hosts
```

Sortie : `web1.lab`, `web2.lab`. Le **wildcard `*`** matche n'importe quelle suite de caractères.

```bash
ansible '*1.lab' -i inventory/hosts.yml --list-hosts
```

Sortie : `web1.lab`, `db1.lab`. Tous les hôtes qui finissent par `1.lab`.

## 📚 Exercice 7 — Combinaisons complexes

```bash
ansible 'prod:!monitoring' -i inventory/hosts.yml --list-hosts
```

Sortie : `web1.lab`, `web2.lab`. Tous les hôtes de prod **sauf** ceux dans monitoring (db1).

```bash
ansible 'webservers:dbservers:!staging' -i inventory/hosts.yml --list-hosts
```

Sortie : `web2.lab`, `db1.lab`. Union de webservers et dbservers, **moins** ceux dans staging (web1).

🔍 **Observation** : les opérateurs s'évaluent **de gauche à droite**. Pour des patterns complexes, **tester avec `--list-hosts` avant** de lancer le vrai playbook.

## 📚 Exercice 8 — `--limit` sur un playbook

`--limit` applique le pattern **par-dessus** ce qui est dans `hosts:` du playbook :

```bash
ansible-playbook -i inventory/hosts.yml challenge/solution.yml --limit 'webservers:!web1.lab'
```

Le playbook cible `hosts: all` mais `--limit` réduit à **`web2.lab`** uniquement.

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court — `ansible-lint --profile
  production` le vérifie.
- **Convention de ciblage** : ce lab cible all (4 VMs avec patterns) ; pour adapter à un
  autre groupe, ajustez `hosts:` dans `lab.yml`/`solution.yml` puis relancez.
- **Reset isolé** : `make clean` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Quelle commande lancera une tâche sur **tous les serveurs sauf `web1.lab` et `db1.lab`** ?
2. Comment cibler **uniquement les hôtes présents dans `prod` ET dans `monitoring`** ?
3. Si vous avez 50 webservers nommés `web01` à `web50`, comment cibler **uniquement `web10` à `web20`** ? (Indice : combiner ranges et exclusion).

## 🚀 Challenge final

Le challenge ([`challenge/README.md`](challenge/README.md)) demande d'écrire 3 commandes `ansible-playbook --limit ...` qui posent des fichiers marqueurs **uniquement sur les hôtes attendus** par chaque pattern. Tests automatisés via `pytest+testinfra` :

```bash
pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **Ranges dans les patterns** : `web[01:05].lab` matche `web01.lab` à `web05.lab`.
- **Regex** : préfixer par `~` (`~web[1-3]\.lab`) — peu utilisé mais existe.
- **`ansible-inventory -i ... --list --limit '...'`** : montre le résultat d'un pattern sans exécuter.
- **Précédence** : `:` est un OU, `:&` est ET, `:!` est NOT, évalués de gauche à droite.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/inventaires/patterns-hotes/lab.yml
ansible-lint labs/inventaires/patterns-hotes/challenge/solution.yml
ansible-lint --profile production labs/inventaires/patterns-hotes/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

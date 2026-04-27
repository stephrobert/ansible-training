# Lab 13 — Types collections (listes, dicts, nested)

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

🔗 [**Types collections Ansible : list, dict, nested**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/types-collections/)

Au-delà des types simples (string, int, bool), Ansible utilise massivement des
**structures complexes** : listes (`[1, 2, 3]`), dictionnaires (`{key: value}`), et
combinaisons imbriquées (liste de dicts, dict contenant des listes). Ces structures
sont la base des **inventaires de services**, **configs multi-environnements**, et
**boucles structurées**. La maîtrise du couple **`loop:` + `loop_control:`** sur ces
collections est un des marqueurs RHCE EX294.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Définir** une liste, un dict, et une **liste de dicts** en YAML.
2. **Boucler** sur une liste de dicts avec `loop: + loop_control: label:`.
3. **Filtrer** une boucle avec `when:` sur un champ du dict.
4. **Accéder** aux champs nested via notation pointée (`item.tags[0]`).
5. **Diagnostiquer** un cas où la structure attendue ne matche pas (typo, mauvais niveau).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible web1.lab -m ping
ansible web1.lab -b -m shell -a "rm -f /tmp/service-*.txt /tmp/tag-*.txt"
```

## 📚 Exercice 1 — Liste simple vs dict simple

Créez `lab.yml` :

```yaml
---
- name: Demo types collections
  hosts: web1.lab
  become: true
  vars:
    # Liste simple
    fruits:
      - pomme
      - banane
      - cerise

    # Dictionnaire simple
    db_config:
      host: db1.lab
      port: 5432
      name: myapp_db
  tasks:
    - name: Iterer sur la liste fruits
      ansible.builtin.debug:
        msg: "Fruit : {{ item }}"
      loop: "{{ fruits }}"

    - name: Acceder aux champs du dict
      ansible.builtin.debug:
        msg: "Connect to {{ db_config.host }}:{{ db_config.port }}/{{ db_config.name }}"
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/types-collections/lab.yml
```

🔍 **Observation** :

- `loop: "{{ fruits }}"` → **3 itérations**, `item` est une string.
- `db_config.host` → notation pointée sur un dict simple.

## 📚 Exercice 2 — Liste de dicts (le pattern le plus courant)

Modifiez `lab.yml` pour ajouter une variable `services` :

```yaml
vars:
  services:
    - name: nginx
      port: 80
      enabled: true
      tags: [web, frontend]
    - name: redis
      port: 6379
      enabled: false
      tags: [cache, backend]
    - name: postgresql
      port: 5432
      enabled: true
      tags: [database, backend]
```

Et la tâche associée :

```yaml
- name: Poser un marqueur par service active
  ansible.builtin.copy:
    dest: "/tmp/service-{{ item.name }}.txt"
    content: "Service {{ item.name }} sur port {{ item.port }}, tags={{ item.tags | join(',') }}\n"
    mode: "0644"
  loop: "{{ services }}"
  loop_control:
    label: "{{ item.name }}"
  when: item.enabled
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/types-collections/lab.yml
```

🔍 **Observation** :

- **3 itérations** mais **2 changed** (nginx, postgresql) et **1 skipped** (redis, `enabled: false`).
- **`loop_control: label:`** affiche `[item=nginx]` au lieu du dict complet — sortie console lisible.
- **`item.tags | join(',')`** : transforme la liste de tags en string `web,frontend`.

```bash
ansible web1.lab -b -m shell -a "ls /tmp/service-*.txt && cat /tmp/service-nginx.txt"
```

## 📚 Exercice 3 — Accéder aux champs nested

Testez les **deux notations équivalentes** pour accéder à un champ de dict :

```yaml
- name: Comparer les deux notations d acces
  ansible.builtin.debug:
    msg: |
      Pointee : {{ services[0].name }}
      Bracket : {{ services[0]['name'] }}
      Nested  : {{ services[0].tags[1] }}
```

🔍 **Observation** : les deux notations donnent le même résultat. **Quand préférer
laquelle ?**

- **Pointée** (`var.key`) : plus lisible, mais ne marche pas si la clé contient un
  tiret, un espace, ou commence par un chiffre (`var.my-key` ❌).
- **Bracket** (`var['key']`) : marche toujours, et accepte des **expressions**
  (`var[dynamic_key_name]`).

**En pratique** : pointée par défaut, bracket si la clé contient des caractères spéciaux
ou si la clé est dynamique.

## 📚 Exercice 4 — Filtres Jinja2 sur les collections

Sur la liste de dicts `services`, on veut **extraire** uniquement les services activés
**dans un format simplifié**. Le filtre `selectattr` est l'outil idéal.

```yaml
- name: Extraire les services actives en liste de noms
  ansible.builtin.debug:
    msg: "Actives : {{ services | selectattr('enabled') | map(attribute='name') | list }}"

- name: Filtrer par tag
  ansible.builtin.debug:
    msg: "Services backend : {{ services | selectattr('tags', 'contains', 'backend') | map(attribute='name') | list }}"
```

🔍 **Observation** :

- `selectattr('enabled')` garde les dicts où `enabled` est truthy → `[nginx, postgresql]`.
- `map(attribute='name')` projette sur le champ `name` → `['nginx', 'postgresql']`.
- `selectattr('tags', 'contains', 'backend')` garde ceux dont `tags` contient `backend`
  → `[redis, postgresql]`.

Les filtres Jinja2 sur les collections sont couverts en détail dans **lab 19 (filtres
essentiels)** et **lab 27 (filtres avancés)**.

## 📚 Exercice 5 — Le piège : faux niveau d'imbrication

Reproduire un cas d'erreur classique. Modifiez la variable `services` :

```yaml
services:
  - name: nginx
    port: 80
    config:
      ssl_enabled: true
      certificate: /etc/ssl/cert.pem
```

Et tentez :

```yaml
- name: Faux acces (typo niveau)
  ansible.builtin.debug:
    msg: "Cert: {{ services[0].certificate }}"  # ❌ certificate est sous config
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/types-collections/lab.yml
```

🔍 **Observation** : erreur `'dict object' has no attribute 'certificate'`. Le champ
est sous **`services[0].config.certificate`**, pas directement sous `services[0]`.

**Outil de diagnostic** : utiliser `ansible.builtin.debug: var: services[0]` pour
**afficher la structure complète** d'un élément avant d'écrire les accès.

```yaml
- name: Diagnostiquer la structure
  ansible.builtin.debug:
    var: services[0]
```

## 🔍 Observations à noter

- **Liste de dicts** = pattern le plus courant pour décrire un parc (services, users, packages).
- **`loop_control: label:`** est obligatoire en pratique — sortie illisible sans elle.
- **`when: item.<key>`** filtre les itérations sans deuxième boucle.
- **Notation pointée vs bracket** : pointée par défaut, bracket pour clés spéciales / dynamiques.
- **`selectattr` + `map(attribute=...)`** = l'outil de filtrage / projection sur listes de dicts.

## 🤔 Questions de réflexion

1. Vous avez une liste de 200 services. Vous voulez n'agir que sur ceux dont `tags`
   contient à la fois `backend` ET `production`. Comment exprimez-vous ce filtre ?
   (indice : `selectattr` peut être chaîné).

2. Pourquoi `vars: my_dict: {}` (dict vide) génère-t-il une erreur si vous tentez
   `my_dict.somekey`, alors que sur un dict non-vide la même expression renvoie
   "undefined" sans planter ?

3. Quelle structure choisiriez-vous pour décrire 50 utilisateurs avec leurs droits :
   un **dict de dicts** (`users: {alice: {...}, bob: {...}}`) ou une **liste de dicts**
   (`users: [{name: alice, ...}, {name: bob, ...}]`) ? Quels critères ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`combine`** : fusionner deux dicts. Utile pour **superposer** une config de base
  avec un override.
- **`dict2items`** + **`items2dict`** : convertir un dict en liste de dicts (pour boucler
  dessus) et inversement (pour le re-construire après filtrage).
- **`json_query`** : équivalent de `jq` côté Ansible — pour des extractions complexes
  sur des JSON volumineux (sortie d'un `uri:`).
- **Pattern `defaults + overrides`** : `vars: { app: '{{ app_defaults | combine(app_overrides, recursive=True) }}' }`
  — superposer une config par défaut avec un override par environnement.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/types-collections/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/types-collections/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/types-collections/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

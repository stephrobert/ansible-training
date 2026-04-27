# Lab 21 — Boucles `loop:` (`loop_control`, `dict2items`)

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

🔗 [**Boucles Ansible : loop, loop_control, dict2items**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/boucles-loop/)

`loop:` est la directive moderne (Ansible 2.5+) pour répéter une tâche sur une **liste**
ou un **dict** (via `dict2items`). Elle remplace les anciennes formes `with_items:`,
`with_dict:`, `with_*` (lab 21). `loop_control:` permet d'ajuster l'affichage
(`label`), la pause (`pause`), l'index (`index_var`), et la variable de boucle
(`loop_var`). C'est la base de tout playbook qui crée plusieurs ressources :
utilisateurs, paquets, services, fichiers.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Boucler** sur une liste simple et une liste de dicts.
2. **Utiliser** `loop_control: label:` pour rendre la sortie console lisible.
3. **Boucler** sur un dict via `dict2items`.
4. **Récupérer** l'index avec `loop_control: index_var:`.
5. **Diagnostiquer** un cas où `item` est ambigu (boucle imbriquée).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /tmp/loop-*.txt; userdel -rf alice 2>/dev/null; userdel -rf bob 2>/dev/null; userdel -rf charlie 2>/dev/null; true"
```

## 📚 Exercice 1 — Boucle simple sur liste de strings

Créez `lab.yml` :

```yaml
---
- name: Demo loop simple
  hosts: db1.lab
  become: true
  vars:
    fruits: [pomme, banane, cerise]
  tasks:
    - name: Creer un fichier par fruit
      ansible.builtin.copy:
        content: "Fruit : {{ item }}\n"
        dest: "/tmp/loop-fruit-{{ item }}.txt"
        mode: "0644"
      loop: "{{ fruits }}"
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/boucles-loop/lab.yml
```

🔍 **Observation** : 3 itérations, 3 fichiers créés. La sortie console affiche
`[item=pomme]`, `[item=banane]`, `[item=cerise]` — pour cette structure simple,
c'est lisible. Sur des dicts, on aura besoin de `loop_control: label:`.

## 📚 Exercice 2 — Liste de dicts + `loop_control: label:`

```yaml
- name: Creer 3 users
  hosts: db1.lab
  become: true
  vars:
    users:
      - { name: alice, shell: /bin/bash, enabled: true }
      - { name: bob, shell: /bin/zsh, enabled: false }
      - { name: charlie, shell: /bin/bash, enabled: true }
  tasks:
    - name: Creer les users actifs
      ansible.builtin.user:
        name: "{{ item.name }}"
        shell: "{{ item.shell }}"
        state: present
      loop: "{{ users }}"
      loop_control:
        label: "{{ item.name }}"
      when: item.enabled
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/boucles-loop/lab.yml
```

🔍 **Observation** :

- **3 itérations**, **2 changed** (alice, charlie), **1 skipped** (bob, `enabled: false`).
- La sortie affiche `[item=alice]` au lieu de `[item={'name': 'alice', 'shell': '/bin/bash', ...}]`.

**Sans `loop_control: label:`** la sortie est illisible :

```
[item={'name': 'alice', 'shell': '/bin/bash', 'enabled': True}]
[item={'name': 'bob', 'shell': '/bin/zsh', 'enabled': False}]
```

→ **Toujours** mettre un `label:` dans les boucles sur dicts.

## 📚 Exercice 3 — Boucler sur un dict avec `dict2items`

`loop:` veut une **liste**. Pour boucler sur un **dict**, on utilise le filtre
`dict2items` qui convertit `{a: 1, b: 2}` en `[{key: a, value: 1}, {key: b, value: 2}]`.

```yaml
- name: Demo loop sur dict
  hosts: db1.lab
  become: true
  vars:
    ports:
      nginx: 80
      redis: 6379
      postgresql: 5432
  tasks:
    - name: Creer un fichier par service / port
      ansible.builtin.copy:
        content: "{{ item.key }} ecoute sur le port {{ item.value }}\n"
        dest: "/tmp/loop-port-{{ item.key }}.txt"
        mode: "0644"
      loop: "{{ ports | dict2items }}"
      loop_control:
        label: "{{ item.key }}={{ item.value }}"
```

🔍 **Observation** : `item.key` = `nginx/redis/postgresql`, `item.value` = `80/6379/5432`.
Le `label:` affiche `[item=nginx=80]` — lisible.

## 📚 Exercice 4 — `index_var` et `pause`

```yaml
- name: Demo index_var et pause
  hosts: db1.lab
  become: true
  vars:
    items_list: [un, deux, trois, quatre, cinq]
  tasks:
    - name: Iteration avec index
      ansible.builtin.copy:
        content: "Item {{ idx }} : {{ item }}\n"
        dest: "/tmp/loop-indexed-{{ idx }}.txt"
        mode: "0644"
      loop: "{{ items_list }}"
      loop_control:
        label: "{{ idx }}/{{ items_list | length }}"
        index_var: idx
        pause: 1
```

🔍 **Observation** :

- **`index_var: idx`** = nom de la variable d'index (par défaut, pas exposé). Permet
  de générer des noms uniques `loop-indexed-0.txt`, `loop-indexed-1.txt`, etc.
- **`pause: 1`** = attente de 1 seconde **entre chaque itération**. Utile pour des
  appels API rate-limités, ou des opérations longues à étaler.

## 📚 Exercice 5 — Boucle imbriquée et `loop_var`

Quand vous avez **deux boucles imbriquées** (ex : un block dans une boucle qui
contient lui-même une boucle), `item` devient ambigu — il faut renommer.

```yaml
- name: Demo boucles imbriquees
  hosts: db1.lab
  become: true
  vars:
    users:
      - { name: alice, files: [.bashrc, .vimrc] }
      - { name: bob, files: [.bashrc] }
  tasks:
    - name: Creer fichier marker pour chaque user/file combination
      block:
        - name: Inner loop sur les fichiers du user courant
          ansible.builtin.debug:
            msg: "User {{ user_item.name }}, file {{ file_item }}"
          loop: "{{ user_item.files }}"
          loop_control:
            loop_var: file_item
      loop: "{{ users }}"
      loop_control:
        loop_var: user_item
        label: "{{ user_item.name }}"
```

🔍 **Observation** : `loop_var: user_item` renomme `item` de la boucle externe en
`user_item`, et `loop_var: file_item` renomme la boucle interne en `file_item`.
Sans ces renommages, l'inner aurait écrasé `item` de l'outer — bug silencieux.

## 📚 Exercice 6 — Le piège : `loop` avec une string (pas une liste)

```yaml
- name: Piege loop sur string
  vars:
    not_a_list: "abc"
  ansible.builtin.debug:
    msg: "Item : {{ item }}"
  loop: "{{ not_a_list }}"
```

🔍 **Observation** : Ansible itère **caractère par caractère** ! Output :

```
[item=a]
[item=b]
[item=c]
```

Une **string est itérable** en Python, mais ce n'est généralement pas ce qu'on veut.

**Solutions** :

```yaml
# Forcer une liste a 1 element
loop: "{{ [not_a_list] }}"

# Ou tester si c est deja une liste
loop: "{{ not_a_list if not_a_list is sequence and not_a_list is not string else [not_a_list] }}"
```

## 🔍 Observations à noter

- **`loop:`** remplace tous les `with_*` legacy (depuis Ansible 2.5).
- **`loop_control: label:`** est **obligatoire en pratique** sur les boucles de dicts.
- **`dict2items`** convertit un dict en liste `[{key, value}]` pour boucler dessus.
- **`index_var:`** + **`pause:`** = options utiles pour le rythme et l'identification.
- **`loop_var:`** est obligatoire pour les boucles imbriquées.
- **`loop:` sur une string** itère caractère par caractère — piège fréquent.

## 🤔 Questions de réflexion

1. Vous voulez créer des fichiers `/etc/myapp/conf.d/<name>.conf` à partir d'une
   liste de dicts `{name, content}`. Comment articulez-vous `loop:`, `template:`,
   et `loop_control:` ?

2. `loop:` accepte une string et itère caractère par caractère. Comment **forcer**
   `loop:` à toujours traiter sa valeur comme **une seule itération** (qu'elle soit
   string ou liste à 1 élément) ?

3. Vous bouclez sur 100 packages avec `package:` + `loop:`. C'est lent. Pourquoi
   `package: name: [...]` (sans loop) est-il bien plus rapide ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`loop_control: extended: true`** : expose `ansible_loop` avec
  `index`, `index0`, `first`, `last`, `length`, `revindex`, `previtem`, `nextitem`.
  Très utile pour des templates Jinja2 conditionnels (last item sans virgule, etc.).
- **`until:` + `retries:` + `delay:`** : retry d'une tâche jusqu'à condition
  satisfaite. Différent de `loop:` (qui itère sur des données).
- **Pattern flatten** : `loop: "{{ [list1, list2] | flatten }}"` pour fusionner
  plusieurs listes en une seule boucle.
- **`subelements`** : boucler sur des **sous-éléments** d'une liste de dicts —
  équivalent du SQL `JOIN`. Voir lab 21 (with-deprecated) pour la migration depuis
  `with_subelements`.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/boucles-loop/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/boucles-loop/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/boucles-loop/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

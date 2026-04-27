# Lab 22 — Boucles legacy `with_*` (à migrer vers `loop:`)

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

🔗 [**Boucles legacy Ansible : with_items, with_dict, migration vers loop:**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/boucles-with-deprecated/)

Avant Ansible 2.5, on utilisait `with_items:`, `with_dict:`, `with_subelements:`,
`with_fileglob:`, `with_nested:`, etc. Depuis 2.5, **`loop:`** couplé à des **filtres
Jinja2** (`dict2items`, `subelements`, `product`) couvre tous les cas. Les `with_*`
**continuent de fonctionner** mais sont considérés **legacy** par Ansible et la
RHCE 2026. Ce lab montre les **équivalences** pour migrer un code existant.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Reconnaître** les principales formes `with_items`, `with_dict`, `with_subelements`,
   `with_fileglob`, `with_nested`.
2. **Migrer** chaque forme vers son équivalent `loop:` + filtre Jinja2.
3. **Utiliser** `ansible-lint --fix` pour automatiser la migration sur du code existant.
4. **Diagnostiquer** les rares cas où la migration change la sémantique.
5. **Appliquer** la table de correspondance sur un code legacy fourni.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /tmp/withloop-*.txt /tmp/legacy-*.txt"
```

## 📚 Exercice 1 — `with_items` → `loop:` (le plus simple)

```yaml
---
- name: Demo migration with_items
  hosts: db1.lab
  become: true
  tasks:
    - name: Forme legacy with_items
      ansible.builtin.copy:
        dest: "/tmp/legacy-{{ item }}.txt"
        content: "{{ item }}\n"
        mode: "0644"
      with_items: [pomme, banane, cerise]

    - name: Forme moderne loop
      ansible.builtin.copy:
        dest: "/tmp/loop-{{ item }}.txt"
        content: "{{ item }}\n"
        mode: "0644"
      loop: [pomme, banane, cerise]
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/boucles-with-deprecated/lab.yml
```

🔍 **Observation** : les **deux formes** produisent **les mêmes fichiers**.
Comportement strictement équivalent. La différence est purement syntaxique.

## 📚 Exercice 2 — `with_dict` → `loop: + dict2items`

```yaml
- name: with_dict legacy
  ansible.builtin.copy:
    dest: "/tmp/legacy-port-{{ item.key }}.txt"
    content: "{{ item.key }} -> {{ item.value }}\n"
  with_dict:
    nginx: 80
    redis: 6379

- name: loop + dict2items moderne
  ansible.builtin.copy:
    dest: "/tmp/loop-port-{{ item.key }}.txt"
    content: "{{ item.key }} -> {{ item.value }}\n"
  loop: "{{ {'nginx': 80, 'redis': 6379} | dict2items }}"
```

🔍 **Observation** : `with_dict:` consomme un **dict directement** ; `loop:` veut
une **liste** donc on passe par `dict2items` qui produit
`[{key: nginx, value: 80}, ...]`. Output identique.

## 📚 Exercice 3 — `with_fileglob` → `loop: + query('fileglob')`

```yaml
- name: with_fileglob legacy
  ansible.builtin.copy:
    src: "{{ item }}"
    dest: "/tmp/legacy-glob-{{ item | basename }}"
  with_fileglob:
    - "files/*.conf"

- name: loop + query fileglob moderne
  ansible.builtin.copy:
    src: "{{ item }}"
    dest: "/tmp/loop-glob-{{ item | basename }}"
  loop: "{{ query('fileglob', 'files/*.conf') }}"
```

🔍 **Observation** : `with_fileglob:` est remplacé par **`query('fileglob', ...)`**
qui retourne une liste de chemins. **`query`** est préféré à **`lookup`** ici parce
qu'il retourne **toujours une liste** (même vide), idéal pour `loop:`.

## 📚 Exercice 4 — `with_subelements` → `loop: + subelements`

```yaml
- name: Demo subelements
  vars:
    users:
      - name: alice
        ssh_keys:
          - "ssh-ed25519 AAAA1 alice-laptop"
          - "ssh-ed25519 AAAA2 alice-server"
      - name: bob
        ssh_keys:
          - "ssh-ed25519 BBBB1 bob-laptop"
  tasks:
    - name: with_subelements legacy
      ansible.builtin.debug:
        msg: "{{ item.0.name }} a la cle {{ item.1 }}"
      with_subelements:
        - "{{ users }}"
        - ssh_keys

    - name: loop + subelements moderne
      ansible.builtin.debug:
        msg: "{{ item.0.name }} a la cle {{ item.1 }}"
      loop: "{{ users | subelements('ssh_keys') }}"
```

🔍 **Observation** : `subelements` produit une **liste de paires `(parent, child)`** :

```
[
  ({name: alice, ssh_keys: [...]}, "ssh-ed25519 AAAA1 alice-laptop"),
  ({name: alice, ssh_keys: [...]}, "ssh-ed25519 AAAA2 alice-server"),
  ({name: bob, ssh_keys: [...]}, "ssh-ed25519 BBBB1 bob-laptop"),
]
```

Pattern essentiel pour : **users + leurs clés SSH**, **services + leurs ports**,
**fichiers + leurs templates**.

## 📚 Exercice 5 — `with_nested` → `loop: + product | list`

```yaml
- name: with_nested legacy
  ansible.builtin.debug:
    msg: "{{ item.0 }} et {{ item.1 }}"
  with_nested:
    - [a, b]
    - [1, 2]
  # Iterations : (a,1), (a,2), (b,1), (b,2)

- name: loop + product moderne
  ansible.builtin.debug:
    msg: "{{ item.0 }} et {{ item.1 }}"
  loop: "{{ ['a', 'b'] | product([1, 2]) | list }}"
```

🔍 **Observation** : `product` (filtre Jinja2) produit le **produit cartésien** —
toutes les combinaisons. Pratique pour : **users × hosts**, **services × environments**.

## 📚 Exercice 6 — Migration automatique avec `ansible-lint`

Sur du code legacy existant, **`ansible-lint --fix`** peut migrer automatiquement
la plupart des `with_*`.

```bash
# Reperer les with_* dans le repo
grep -rn "with_items\|with_dict\|with_fileglob\|with_subelements\|with_nested" labs/

# Tester sans modifier
ansible-lint labs/ecrire-code/boucles-with-deprecated/lab.yml --offline

# Migration automatique (modifie le fichier)
ansible-lint --fix labs/ecrire-code/boucles-with-deprecated/lab.yml
```

🔍 **Observation** : `ansible-lint --fix` détecte la rule **`use-loop`** et propose
la migration. Sur des cas simples (`with_items`, `with_dict`), la migration est
exacte. Sur `with_subelements` ou `with_nested`, la migration peut nécessiter une
relecture humaine.

**Toujours** :

- **Backup** avant `--fix` (commit git intermédiaire).
- **Tests** après pour vérifier l'équivalence sémantique.

## 📚 Exercice 7 — Le piège : `with_random_choice` n'a pas d'équivalent direct

`with_random_choice:` retourne **un** élément aléatoire d'une liste, **pas** une
itération sur la liste.

```yaml
# Legacy : retourne UN element aleatoire
- name: with_random_choice legacy
  ansible.builtin.debug:
    msg: "Item : {{ item }}"
  with_random_choice: [a, b, c, d]
  # Itere une seule fois sur un element au hasard

# Moderne : utiliser le filtre random + boucle a 1 element
- name: loop avec random
  ansible.builtin.debug:
    msg: "Item : {{ item }}"
  loop: "{{ ['a', 'b', 'c', 'd'] | random | list }}"
```

🔍 **Observation** : la migration nécessite de comprendre **l'intention** du `with_random_choice` (1 itération sur 1 élément aléatoire) — pas d'équivalent
syntaxiquement direct, on enveloppe dans une liste.

## 🔍 Observations à noter

- **`loop:` remplace tous les `with_*`** depuis Ansible 2.5.
- **`with_dict:`** → **`loop: + dict2items`**.
- **`with_fileglob:`** → **`loop: + query('fileglob', ...)`**.
- **`with_subelements:`** → **`loop: + subelements`** (filtre Jinja2).
- **`with_nested:`** → **`loop: + product | list`**.
- **`ansible-lint --fix`** automatise la migration sur les cas simples.
- **Pas de migration directe** pour `with_random_choice`, `with_first_found`, etc.

## 🤔 Questions de réflexion

1. Pourquoi Ansible n'a-t-il **pas déprécié** les `with_*` (juste "legacy") ? Quel
   serait le coût d'un retrait pur et simple ?

2. La forme `with_items: "{{ packages }}"` (avec interpolation) marche depuis
   longtemps. La forme `loop: "{{ packages }}"` aussi. Quelle est la **différence
   technique** entre les deux ? (indice : voir le concept de `lookup` plugin).

3. Vous reprenez un playbook avec 50 `with_*`. Vous lancez `ansible-lint --fix`.
   Quels sont les **3 contrôles à faire** avant de commit ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **Performance** : aucune différence mesurable entre `with_*` et `loop:` —
  l'argument "loop est plus rapide" est faux. La vraie différence est sémantique
  et standardisation.
- **Migration de code legacy** : combiner `ansible-lint --fix` + tests fonctionnels
  + Molecule. Pour un repo de 100 rôles, prévoir 1-2 jours de validation.
- **`use_loop` rule** : règle ansible-lint qui détecte les `with_*` (sauf
  `with_first_found` et `with_random_choice` qui sont conservés pour leur sémantique
  particulière).
- **RHCE 2026** : préférer `loop:` sur tout nouveau code. Les `with_*` ne sont **pas
  pénalisés** sur l'examen mais le **style attendu** est `loop:`.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/boucles-with-deprecated/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/boucles-with-deprecated/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/boucles-with-deprecated/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

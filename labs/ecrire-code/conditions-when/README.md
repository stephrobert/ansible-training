# Lab 20 — Conditions `when:`

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

🔗 [**Conditions Ansible : when, opérateurs, multi-conditions**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/conditions-when/)

`when:` filtre l'exécution d'une tâche selon une **expression booléenne Jinja2**.
Sans condition, la tâche tourne sur tous les hôtes ciblés. Avec `when:`, elle ne
tourne que sur ceux qui satisfont l'expression. Les conditions sont l'**outil n°1
de la programmation Ansible** — multi-OS, déploiement progressif, branches
conditionnelles. Particularité : pas de `{{ }}` dans `when:` — l'expression est
**déjà** Jinja2.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Conditionner** une tâche sur un fact (`ansible_distribution`, version OS).
2. **Combiner** plusieurs conditions avec `and`, `or`, parenthèses.
3. **Tester** la définition d'une variable (`is defined`, `is not defined`).
4. **Utiliser** les tests Jinja2 (`is mapping`, `is sequence`, `is regex`).
5. **Diagnostiquer** un `when:` qui matche faux (souvent un type bool vs string).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ping
ansible all -b -m shell -a "rm -f /tmp/when-*.txt"
```

## 📚 Exercice 1 — Condition simple sur un fact

Créez `lab.yml` :

```yaml
---
- name: Demo when sur fact OS
  hosts: all
  become: true
  gather_facts: true
  tasks:
    - name: Tache RHEL/AlmaLinux/Rocky uniquement
      ansible.builtin.copy:
        content: "Famille redhat\n"
        dest: /tmp/when-redhat.txt
        mode: "0644"
      when: ansible_os_family == "RedHat"

    - name: Tache version major >= 9
      ansible.builtin.copy:
        content: "Version majeur {{ ansible_distribution_major_version }}\n"
        dest: /tmp/when-version.txt
        mode: "0644"
      when: ansible_distribution_major_version | int >= 9
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/conditions-when/lab.yml
```

🔍 **Observation** : sur AlmaLinux 10.1, les **2 tâches s'exécutent**. Les fichiers
sont créés sur web1, web2, db1. Si vous aviez un Debian dans le lab, **aucune** des
deux tâches ne tournerait dessus.

**Pas de `{{ }}` dans `when:`** :

```yaml
when: ansible_os_family == "RedHat"     # ✅
when: "{{ ansible_os_family == 'RedHat' }}"   # ❌ Ansible warning
```

## 📚 Exercice 2 — Combiner avec `and`, `or`

```yaml
- name: AlmaLinux ET version 10
  ansible.builtin.copy:
    content: "AlmaLinux 10\n"
    dest: /tmp/when-and.txt
    mode: "0644"
  when:
    - ansible_distribution == "AlmaLinux"
    - ansible_distribution_major_version | int == 10

- name: RHEL OU AlmaLinux (operator or explicite)
  ansible.builtin.copy:
    content: "RHEL ou AlmaLinux\n"
    dest: /tmp/when-or.txt
    mode: "0644"
  when: ansible_distribution == "RedHat" or ansible_distribution == "AlmaLinux"
```

🔍 **Observation** : la **liste sous `when:`** (forme YAML avec tirets) est un **AND
implicite** entre les conditions. Pour faire un `OR`, il faut écrire l'opérateur
explicitement sur une seule ligne.

**Parenthèses pour la priorité** :

```yaml
when: (ansible_os_family == "RedHat" and ansible_distribution_major_version | int >= 9) or
      (ansible_os_family == "Debian" and ansible_distribution_major_version | int >= 11)
```

## 📚 Exercice 3 — Tester la définition d'une variable

```yaml
- name: Tache si optional_var defini
  ansible.builtin.copy:
    content: "Variable optional_var = {{ optional_var }}\n"
    dest: /tmp/when-defined.txt
    mode: "0644"
  when: optional_var is defined

- name: Tache si optional_var absent
  ansible.builtin.copy:
    content: "optional_var n est pas defini\n"
    dest: /tmp/when-undefined.txt
    mode: "0644"
  when: optional_var is not defined
```

**Lancez d'abord SANS la variable** :

```bash
ansible-playbook labs/ecrire-code/conditions-when/lab.yml
```

🔍 **Observation** : seule la deuxième tâche tourne (`/tmp/when-undefined.txt`
créé, `/tmp/when-defined.txt` skippé).

**Relancez AVEC la variable** :

```bash
ansible-playbook labs/ecrire-code/conditions-when/lab.yml \
  --extra-vars "optional_var=hello"
```

🔍 **Observation** : c'est l'inverse — le fichier `when-defined.txt` est créé.

## 📚 Exercice 4 — Tests sur les types (`is mapping`, `is sequence`)

```yaml
- name: Tester le type de variable
  vars:
    config_dict: {host: db1, port: 5432}
    config_list: [a, b, c]
    config_string: "hello"
  block:
    - name: Test mapping (dict)
      ansible.builtin.debug:
        msg: "config_dict est un dict"
      when: config_dict is mapping

    - name: Test sequence (list)
      ansible.builtin.debug:
        msg: "config_list est une liste"
      when: config_list is sequence and config_list is not string

    - name: Test string
      ansible.builtin.debug:
        msg: "config_string est une string"
      when: config_string is string
```

🔍 **Observation** : tests utiles pour des **tâches polymorphes** qui acceptent une
string OU une liste, par exemple. Combiné avec `default`, on peut écrire :

```yaml
loop: "{{ packages if packages is sequence else [packages] }}"
```

Ce pattern accepte `packages: nginx` (string unique) **ou** `packages: [nginx, redis]`
(liste).

## 📚 Exercice 5 — Conditionner une boucle (`when:` sur l'item)

```yaml
- name: Creer uniquement les services enabled
  ansible.builtin.debug:
    msg: "Service {{ item.name }} sur port {{ item.port }}"
  loop:
    - { name: nginx, port: 80, enabled: true }
    - { name: redis, port: 6379, enabled: false }
    - { name: postgresql, port: 5432, enabled: true }
  when: item.enabled
```

🔍 **Observation** : `when:` peut référencer **`item`** dans une boucle. La tâche
saute redis (`enabled: false`) — c'est `skipped`, pas `changed`.

**Combinaison avec un fact** :

```yaml
loop: "{{ services }}"
when:
  - item.enabled
  - ansible_distribution == "AlmaLinux"
  - item.os_compatible | default(['all']) | contains(ansible_distribution)
```

## 📚 Exercice 6 — Le piège : type bool vs string

Cas surprenant : `when: app_enabled` peut **toujours être vrai** même quand on attend
"false".

```yaml
- name: Demo piege type
  vars:
    app_enabled_str: "false"   # string "false"
    app_enabled_bool: false    # bool false
  block:
    - name: Tache avec string
      ansible.builtin.debug:
        msg: "Tache avec string false"
      when: app_enabled_str
      # ATTENTION : tourne ! Une string non vide est truthy en Python

    - name: Tache avec bool
      ansible.builtin.debug:
        msg: "Tache avec bool false"
      when: app_enabled_bool
      # OK : ne tourne pas
```

🔍 **Observation** : `when: "false"` (string) → **truthy** (toute string non-vide
est truthy). `when: false` (bool) → falsy.

**Source du piège** : `--extra-vars "app_enabled=false"` passe une **string** (la CLI
ne fait pas de typage YAML). La valeur réelle est `"false"`, pas `False`.

**Solution** : forcer le bool avec le filtre `bool` :

```yaml
when: app_enabled | bool
```

`| bool` reconnaît `'true'`, `'yes'`, `'1'` comme vrai et `'false'`, `'no'`, `'0'`
comme faux.

## 🔍 Observations à noter

- **`when:`** = expression Jinja2 **sans `{{ }}`**.
- **Liste sous `when:`** = AND implicite entre les éléments.
- **`is defined` / `is not defined`** = tester l'existence d'une variable.
- **`is mapping` / `is sequence` / `is string`** = tester le type.
- **`when: var | bool`** = forcer la conversion en bool (évite le piège string truthy).
- **`when:` dans un `loop:`** = filtre par item, pas par tâche.

## 🤔 Questions de réflexion

1. Vous avez un playbook qui doit tourner sur **RHEL 9+** **OU** **Debian 11+**.
   Comment écrivez-vous le `when:` (combinaison `and` / `or` / parenthèses) ?

2. `when: my_dict.field is defined` retourne **vrai** même quand `my_dict.field`
   est `null`. Quelle est la différence entre "défini" et "non null" ?

3. Pourquoi `--extra-vars "app_enabled=false"` peut-il faire **tourner** une tâche
   conditionnée par `when: app_enabled` ? Quelle est la mitigation propre ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`when:` sur un block** : applique la condition à toutes les tâches du block.
  Plus DRY que de répéter la même condition sur 5 tâches.
- **`failed_when:` + `when:`** : combiner pour fabriquer une logique d'audit
  complexe (ex : échouer si un fichier obligatoire est absent ET sur RHEL 9+).
- **Tests custom** (`is regex`, `is search`) : matcher une regex sur une string.
  `when: ansible_kernel is search('5\\.14')`.
- **Pattern `vars_prompt:` + `when:`** : conditionner sur une réponse interactive
  utilisateur (rare mais utile pour des plays one-shot).

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/conditions-when/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/conditions-when/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/conditions-when/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

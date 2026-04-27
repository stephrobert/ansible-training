# Lab 53 — Modules `assert:` et `fail:` (validation défensive)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.

## 🧠 Rappel

🔗 [**Modules assert et fail Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/assert-fail/)

Deux modules complémentaires pour la **programmation défensive** :

- **`ansible.builtin.assert:`** valide une **condition** ; si elle est fausse, le
  play échoue avec un message clair. Pattern de **précondition** en début de play.
- **`ansible.builtin.fail:`** échoue **explicitement** avec un message custom.
  Pattern de **branche d'erreur** dans une logique conditionnelle.

Différence sémantique : `assert:` exprime "ça **doit** être vrai" ; `fail:`
exprime "j'arrête **maintenant** parce que telle condition est rencontrée".

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Valider** des **prérequis** en début de play avec `assert:`.
2. **Personnaliser** les messages avec `fail_msg:` / `success_msg:`.
3. **Échouer explicitement** avec `fail:` + `when:` (branche d'erreur).
4. **Combiner** `assert:` avec **tests Jinja2** (`is defined`, `is integer`).
5. **Choisir** entre `assert:`, `fail:`, et `failed_when:` selon le contexte.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
```

## 📚 Exercice 1 — `assert:` simple

Créez `lab.yml` :

```yaml
---
- name: Demo assert
  hosts: db1.lab
  vars:
    app_port: 8080
  tasks:
    - name: Valider que app_port est dans la plage non-privilegiee
      ansible.builtin.assert:
        that:
          - app_port is defined
          - app_port is integer
          - app_port > 1024
          - app_port < 65535
        fail_msg: "app_port doit etre un entier entre 1024 et 65535 (recu : {{ app_port | default('absent') }})"
        success_msg: "Validation OK : app_port = {{ app_port }}"
```

**Lancez** :

```bash
ansible-playbook labs/modules-diagnostic/assert-fail/lab.yml
```

🔍 **Observation** :

- Si **toutes les conditions** sont vraies → `success_msg` affiché, play continue.
- Si **une condition échoue** → `fail_msg` affiché, play **failed**.

**Tester l'échec** :

```bash
ansible-playbook labs/modules-diagnostic/assert-fail/lab.yml \
  --extra-vars "app_port=42"
# → fail_msg : app_port doit etre un entier entre 1024 et 65535 (recu : 42)
```

## 📚 Exercice 2 — Variables magiques `that:`

```yaml
- name: Valider plusieurs aspects de l environnement
  ansible.builtin.assert:
    that:
      - ansible_distribution in ['AlmaLinux', 'RedHat', 'Rocky']
      - ansible_distribution_major_version | int >= 9
      - ansible_memtotal_mb >= 1024
      - 'wheel' in (ansible_local | default({}) | dict2items | map(attribute='value') | list | flatten | default([]))
    fail_msg: |
      Pre-requis non remplis :
      - OS attendu : RHEL/AlmaLinux/Rocky 9+ (vu : {{ ansible_distribution }} {{ ansible_distribution_major_version }})
      - Memoire min : 1Go (vu : {{ ansible_memtotal_mb }} Mo)
```

🔍 **Observation** : `that:` accepte une **liste** de conditions = AND
implicite. **`fail_msg:`** peut être multi-ligne pour un diagnostic complet.

## 📚 Exercice 3 — `fail:` (échec explicite avec when)

```yaml
- name: Detecter un environnement non supporte
  ansible.builtin.fail:
    msg: |
      Environnement non supporte :
      - OS : {{ ansible_distribution }}
      - Version : {{ ansible_distribution_version }}
      Ce playbook necessite RHEL/AlmaLinux 9+.
  when: ansible_distribution not in ['AlmaLinux', 'RedHat', 'Rocky']
        or ansible_distribution_major_version | int < 9
```

🔍 **Observation** : **`fail:`** est une tâche qui **échoue toujours** (quand
elle s'exécute). `when:` la conditionne. Pattern de **branche d'erreur**
explicite.

**`assert:` vs `fail:` + `when:`** :

```yaml
# Equivalent fonctionnel
- ansible.builtin.assert:
    that: ansible_distribution_major_version | int >= 9
    fail_msg: "RHEL 9+ requis"

- ansible.builtin.fail:
    msg: "RHEL 9+ requis"
  when: ansible_distribution_major_version | int < 9
```

**Préférer `assert:`** quand la **condition est positive** ("ça doit être vrai").
**Préférer `fail:`** quand la logique est **branche d'erreur** explicite (ex :
"si l'OS est X, on ne supporte pas").

## 📚 Exercice 4 — Pattern précondition de play

```yaml
- name: Deploy myapp
  hosts: webservers
  become: true
  pre_tasks:
    - name: Pre-requis - OS
      ansible.builtin.assert:
        that:
          - ansible_distribution in ['AlmaLinux', 'RedHat', 'Rocky']
        fail_msg: "OS non supporte"

    - name: Pre-requis - paquets installes
      ansible.builtin.command: rpm -q chrony firewalld
      register: pkgs_check
      changed_when: false
      failed_when: pkgs_check.rc != 0

    - name: Pre-requis - port libre
      ansible.builtin.wait_for:
        port: 8080
        host: 127.0.0.1
        state: stopped
        timeout: 5

  tasks:
    # ... vraies taches de deploy
```

🔍 **Observation** : `pre_tasks:` est une section dédiée aux **préconditions**.
Si une `assert:` failed dedans, les `tasks:` ne tournent **pas**. Pattern
**fail-fast** propre.

## 📚 Exercice 5 — Tests Jinja2 dans `assert:`

```yaml
- name: Valider la structure d une variable complexe
  vars:
    db_config:
      host: db1.lab
      port: 5432
      pool_size: 10
  ansible.builtin.assert:
    that:
      - db_config is defined
      - db_config is mapping              # est un dict
      - db_config.host is defined
      - db_config.host is string
      - db_config.port is defined
      - db_config.port is integer
      - db_config.port > 0
      - db_config.port < 65536
      - db_config.pool_size is integer
      - db_config.pool_size > 0
    fail_msg: "Structure de db_config invalide — voir les conditions ci-dessus"
```

🔍 **Observation** : pattern **schema validation** à la main. Pour des cas
complexes, on combine **plusieurs tests** (`is defined`, `is mapping`, `is
integer`). Voir [Lab 28 — Tests Jinja2](../28-ecrire-code-tests-jinja/) pour la liste
complète.

## 📚 Exercice 6 — Le piège : `assert:` après `register:`

```yaml
- name: Capturer le rc de openssl
  ansible.builtin.command: openssl version
  register: openssl_check
  changed_when: false
  failed_when: false   # Capturer meme en cas d echec

- name: Valider que la version est >= 3
  ansible.builtin.assert:
    that:
      - openssl_check.rc == 0
      - openssl_check.stdout is search('OpenSSL 3\\.')
    fail_msg: "OpenSSL 3+ requis (vu : {{ openssl_check.stdout | default('non installe') }})"
```

🔍 **Observation** : pattern **command + register + assert** très courant pour
valider une version de binaire avant utilisation. Le `failed_when: false` sur
le `command:` permet à `assert:` de générer le **message d'erreur clair** au
lieu de l'erreur brute du module.

## 📚 Exercice 7 — `quiet: true` pour les asserts en cascade

Sur des dizaines d'assertions, le bruit dans la sortie est gênant. **`quiet:
true`** affiche **uniquement** les `fail_msg:` (pas les success).

```yaml
- name: 50 validations silencieuses
  ansible.builtin.assert:
    that:
      - ansible_memtotal_mb >= 1024
    fail_msg: "Memoire insuffisante"
    success_msg: "Memoire OK"
    quiet: true
```

🔍 **Observation** : avec `quiet: true`, l'assert ne pollue les logs que si
elle échoue. Sortie console plus lisible sur les playbooks de **conformité**
(CIS Benchmark, audit RGS).

## 🔍 Observations à noter

- **`assert: that:`** = liste de conditions, AND implicite.
- **`fail_msg:`** / **`success_msg:`** pour personnaliser les messages.
- **`fail:`** = échec explicite, à combiner avec `when:`.
- **Préférer `assert:`** pour les **préconditions** ("ça doit être vrai").
- **Préférer `fail:`** pour les **branches d'erreur** ("si X alors abort").
- **`pre_tasks:`** est la section idiomatique pour les `assert:` de
  validation.
- **`quiet: true`** sur assert pour éviter la pollution sur les playbooks
  d'audit.

## 🤔 Questions de réflexion

1. Vous voulez **valider 10 conditions** en parallèle. Préférez-vous un
   `assert: that: [c1, c2, ..., c10]` ou 10 `assert:` séparés ? Quel
   compromis ?

2. Différence sémantique entre `failed_when: rc != 0` (sur un `command:`) et
   `assert: that: rc == 0` (en tâche suivante) ?

3. Vous voulez **continuer le play** même si l'assert échoue (pour collecter
   tous les warnings). Quel pattern (`ignore_errors:`, `block/rescue`, ou
   custom) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`debug: msg:`** pour afficher sans échouer (équivalent `print` Python).
- **`pause: prompt:`** pour demander une **confirmation interactive** avant
  une opération critique.
- **`meta: end_play`** pour terminer le play **proprement** sans erreur quand
  une condition est rencontrée (différent de `fail:` qui retourne `failed=1`).
- **Pattern `assert + when`** : `when: var | bool` sur une `assert:` pour la
  conditionner aux runs où elle est pertinente.
- **Lab 51 (`stat:`) + `assert:`** : combinaison puissante — vérifier
  l'existence + valider les attributs.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/modules-diagnostic/assert-fail/lab.yml
ansible-lint labs/modules-diagnostic/assert-fail/challenge/solution.yml
ansible-lint --profile production labs/modules-diagnostic/assert-fail/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

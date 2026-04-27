# Lab 24 — `failed_when:` et `changed_when:` (redéfinir succès et changement)

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

🔗 [**failed_when et changed_when Ansible : redéfinir succès et changement**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/failed-when-changed-when/)

Par défaut, Ansible considère qu'une tâche `command:` ou `shell:` est **`failed`**
si le code retour (`rc`) est différent de 0, et **`changed`** dans tous les cas.
Ces deux comportements peuvent être **redéfinis** :

- **`failed_when:`** = expression qui, si vraie, marque la tâche comme `failed`.
- **`changed_when:`** = expression qui, si vraie, marque la tâche comme `changed`.

Ces deux directives sont **essentielles pour rendre `command:`/`shell:` idempotents**
— sans elles, une commande shell est **toujours `changed`**, ce qui pollue les logs
et fait sauter les handlers à tort.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Désactiver** le `changed` par défaut sur les commandes lecture-seule (`changed_when: false`).
2. **Définir** un `changed_when:` basé sur la sortie (string match, regex).
3. **Redéfinir** le `failed_when:` pour accepter certains codes retour comme succès.
4. **Combiner** `failed_when: + changed_when:` pour un module idempotent.
5. **Diagnostiquer** un module qui rapporte `changed` à tort.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
```

## 📚 Exercice 1 — Le problème : `command:` toujours `changed`

Créez `lab.yml` :

```yaml
---
- name: Demo command toujours changed
  hosts: db1.lab
  become: true
  tasks:
    - name: Lire la version d openssl
      ansible.builtin.command: openssl version
      register: ssl_version
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/failed-when-changed-when/lab.yml
```

🔍 **Observation** : `PLAY RECAP` affiche `changed=1`. Pourtant, **lire** une version
ne **change rien** — la tâche **devrait être `ok=1, changed=0`**. C'est une pollution
classique des logs.

**Pire** : si cette tâche `notify:` un handler, le handler tournerait à chaque run
**à tort** (rechargement de service inutile).

## 📚 Exercice 2 — `changed_when: false` sur les lectures

Modifiez la tâche :

```yaml
- name: Lire la version d openssl (lecture seule)
  ansible.builtin.command: openssl version
  register: ssl_version
  changed_when: false
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/failed-when-changed-when/lab.yml
```

🔍 **Observation** : `PLAY RECAP` affiche maintenant `ok=1, changed=0`. La tâche est
marquée comme **lecture seule** explicitement.

**Règle** : `changed_when: false` sur **toute** commande qui ne fait que lire
(`cat`, `grep`, `openssl version`, `which`, `stat`, etc.).

## 📚 Exercice 3 — `changed_when:` avec expression sur la sortie

Pour des commandes qui peuvent **modifier** ou **non**, utiliser une expression sur
la sortie pour détecter le changement.

Cas réel : `git pull` change quelque chose **uniquement** s'il y a de nouveaux commits.
On peut détecter via la sortie qui contient "Already up to date" ou pas.

```yaml
- name: Simulation git pull (changed seulement si nouveau)
  ansible.builtin.command: |
    echo "{{ 'Already up to date.' if simulate_no_change | default(true) | bool else 'Updating abc..def' }}"
  register: pull_result
  changed_when: "'Already up to date' not in pull_result.stdout"
```

**Lancez** :

```bash
# 1er run : simulate_no_change=true (defaut) → ok=1
ansible-playbook labs/ecrire-code/failed-when-changed-when/lab.yml

# 2eme run : simulate_no_change=false → changed=1
ansible-playbook labs/ecrire-code/failed-when-changed-when/lab.yml \
  --extra-vars "simulate_no_change=false"
```

🔍 **Observation** : la même commande shell rapporte `ok=1` ou `changed=1` selon
sa sortie — c'est l'**idempotence faite à la main** sur un `command:`.

## 📚 Exercice 4 — `failed_when:` pour accepter des codes retour spécifiques

Cas classique : `grep` retourne **`rc=1` quand il ne trouve pas** la chaîne — Ansible
le traite comme un échec. Or, pour un audit, c'est souvent **un succès**.

```yaml
- name: Verifier si root login est desactive (rc 1 = absent = OK)
  ansible.builtin.command: grep -E "^PermitRootLogin no" /etc/ssh/sshd_config
  register: grep_result
  failed_when: grep_result.rc not in [0, 1]
  changed_when: false
```

🔍 **Observation** :

- **rc=0** : trouvé → tâche `ok`.
- **rc=1** : non trouvé → tâche `ok` aussi (parce que `1 in [0, 1]` est vrai, donc `failed_when` est faux).
- **rc=2+** : autre erreur (fichier absent, etc.) → tâche **failed**.

**Sans `failed_when:`**, le `rc=1` aurait fait failer la tâche — vous auriez besoin
d'un `block/rescue` lourd ou `ignore_errors: true` dangereux.

## 📚 Exercice 5 — Combinaison `failed_when: + changed_when:` (idempotence complète)

Pattern complet pour rendre une commande shell **idempotente** (équivalent d'un module
natif) :

```yaml
- name: Activer SELinux en enforcing (idempotent)
  ansible.builtin.shell: |
    current=$(getenforce)
    if [ "$current" != "Enforcing" ]; then
      setenforce 1
      echo "CHANGED"
    else
      echo "OK"
    fi
  register: selinux_result
  changed_when: "'CHANGED' in selinux_result.stdout"
  failed_when: false  # Le shell gere lui-meme les cas
```

🔍 **Observation** :

- 1er run : SELinux pas en enforcing → output `CHANGED` → tâche `changed`.
- 2ème run : déjà en enforcing → output `OK` → tâche `ok`.

C'est exactement comme l'idempotence des **modules builtin** — mais codée à la main
parce que `setenforce` n'a pas de module natif.

**Mieux** : utiliser **`ansible.posix.selinux`** (module dédié) — toujours préférer un
module natif quand il existe.

## 📚 Exercice 6 — Le piège : `failed_when:` mal écrit

```yaml
# ❌ Mauvais : interpretation Jinja2
- name: Mauvaise expression
  ansible.builtin.command: echo hello
  register: r
  failed_when: "{{ r.rc != 0 }}"  # ❌ Pas besoin de {{ }}

# ✅ Bon
- name: Bonne expression
  ansible.builtin.command: echo hello
  register: r
  failed_when: r.rc != 0
```

🔍 **Observation** : `failed_when:` et `changed_when:` sont **déjà des expressions
Jinja2** — ne **pas** ajouter `{{ }}` (Ansible warning depuis 2.16).

**Autre piège** : confusion `or` / `and`. `failed_when: r.rc != 0 or 'Error' in r.stdout`
est plus restrictif que `r.rc != 0` seul. Bien réfléchir à la sémantique.

## 🔍 Observations à noter

- **`changed_when: false`** sur **toute** commande lecture-seule (audit, query).
- **`changed_when:` avec expression** rend `command:` / `shell:` idempotent.
- **`failed_when:` avec liste de codes** = accepter certains rc comme succès.
- **`failed_when:` + `changed_when:`** combinés permettent d'écrire un "module à la main".
- **Pas de `{{ }}` dans `when:`, `failed_when:`, `changed_when:`** — déjà des expressions.
- **Préférer un module natif** quand il existe (selinux, sysctl, lineinfile) plutôt
  que `shell:` + `failed_when` / `changed_when`.

## 🤔 Questions de réflexion

1. Vous lancez `dnf check-update` qui retourne **`rc=100` quand il y a des updates
   disponibles**. Comment écrivez-vous le `failed_when:` pour que `rc=0` (à jour) et
   `rc=100` (updates dispo) soient tous deux des **succès**, mais autres codes failent ?

2. Pourquoi un `changed_when: false` sur une tâche `command:` dans un play **rolling
   update** est-il **important** ? (indice : penser aux handlers).

3. Quelle est la différence entre `failed_when: false` (force le `failed=False`)
   et `ignore_errors: true` (lab 24) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`failed_when:` avec liste** : `failed_when: ['fatal' in r.stderr, r.rc not in [0,1]]`
  est un **OR implicite** entre les conditions de la liste (comme `when:`).
- **`unreachable_when:` n'existe pas** : pour gérer un host injoignable, utiliser
  `block/rescue` au niveau du play ou `serial: + max_fail_percentage:`.
- **`check_mode:` + `changed_when:`** : un `command:` en `--check` ne tourne pas par
  défaut. Forcer avec `check_mode: false` + `changed_when: false` pour un audit
  pendant le check mode (lab 08).
- **Pattern `dry-run` + `apply`** : une seule tâche shell qui prend `--dry-run` selon
  une variable, et utilise `changed_when:` sur la sortie. Permet d'avoir un mode
  test/apply unique.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/failed-when-changed-when/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/failed-when-changed-when/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/failed-when-changed-when/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

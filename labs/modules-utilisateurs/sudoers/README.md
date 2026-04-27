# Lab 43 — Module `sudoers:` (gérer les droits sudo)

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

🔗 [**Module sudoers Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-sudoers/)

`community.general.sudoers:` génère des fichiers dans `/etc/sudoers.d/` avec
**validation automatique** via `visudo -cf`. C'est le **module de référence** pour
gérer les droits sudo de manière idempotente — bien plus sûr qu'un
`lineinfile:` sur `/etc/sudoers` (un fichier mal formé verrouille `sudo` pour
**tous les utilisateurs**).

Ce module appartient à la collection **`community.general`** — sur Ansible Core
2.20, il faut `ansible-galaxy collection install community.general`.

Options principales : **`name:`** (nom du fichier dans `/etc/sudoers.d/`),
**`user:`** ou **`group:`**, **`commands:`**, **`nopassword: true`**, **`state:`**,
**`runas:`**, **`validation:`** (par défaut `detect` qui appelle `visudo -cf`).

> ⚠️ **Important sur `nopassword:`** — depuis `community.general` 11.0, le défaut
> est **`true`** (sudo sans password) ! Pour exiger un password, **explicitement**
> `nopassword: false`. Surprise classique sur les versions récentes.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Créer** une règle sudo simple via le module `sudoers:`.
2. **Limiter** l'accès à des **commandes précises** (principe de moindre
   privilège).
3. **Distinguer** `nopassword: true` (sudo sans password) du défaut (avec
   password).
4. **Gérer** des règles **sur un groupe** plutôt qu'un user individuel.
5. **Pourquoi** ne **jamais** modifier `/etc/sudoers` directement.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible-galaxy collection install community.general
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /etc/sudoers.d/lab-rhce-*; useradd alice -m 2>/dev/null; useradd bob -m 2>/dev/null; groupadd ops-team 2>/dev/null; true"
```

## 📚 Exercice 1 — Pourquoi pas `lineinfile:` sur `/etc/sudoers`

```yaml
# ❌ DANGEREUX
- ansible.builtin.lineinfile:
    path: /etc/sudoers
    line: "alice ALL=(ALL) NOPASSWD:ALL"
```

🔍 **Risques** :

- Si la ligne est **mal formée** (typo, syntaxe sudoers non standard), `/etc/sudoers`
  devient **invalide**.
- `sudo` refuse alors de fonctionner — **personne** ne peut élever ses droits.
- Sur un serveur en production, vous êtes **bloqué** : impossible de revenir
  en arrière sans accès console physique ou IPMI.

**Avec le module `sudoers:`**, la **validation `visudo -cf %s`** est **automatique
et obligatoire** — un fichier invalide n'est **jamais** déposé.

## 📚 Exercice 2 — Création d'une règle simple

Créez `lab.yml` :

```yaml
---
- name: Demo sudoers
  hosts: db1.lab
  become: true
  tasks:
    - name: Donner les droits sudo a alice (avec password)
      community.general.sudoers:
        name: lab-rhce-alice
        user: alice
        commands: ALL
        state: present
```

**Lancez** :

```bash
ansible-playbook labs/modules-utilisateurs/sudoers/lab.yml
ssh ansible@db1.lab 'sudo cat /etc/sudoers.d/lab-rhce-alice'
```

🔍 **Observation** : un fichier `/etc/sudoers.d/lab-rhce-alice` est créé :

```text
alice ALL=(ALL) ALL
```

Le module a :

- **Validé** la syntaxe via `visudo -cf` avant le dépôt.
- **Posé les bonnes permissions** : `0440` (lecture pour `root` uniquement +
  groupe `root`). Si vous tentez `chmod 0644`, sudo **refuse** le fichier.

## 📚 Exercice 3 — Sudo sans password (`nopassword: true`)

```yaml
- name: Bob peut faire SUDO sans password (DANGER)
  community.general.sudoers:
    name: lab-rhce-bob-nopass
    user: bob
    commands: ALL
    nopassword: true
    state: present
```

**Vérifiez le fichier généré** :

```bash
ssh ansible@db1.lab 'sudo cat /etc/sudoers.d/lab-rhce-bob-nopass'
```

🔍 **Observation** :

```text
bob ALL=(ALL) NOPASSWD:ALL
```

**`NOPASSWD:`** = sudo sans demande de password.

**Cas légitimes** :

- **Compte ansible** sur un managed node (`NOPASSWD:ALL` pour tous les modules).
- Compte de **CI/CD** qui doit lancer des commandes sans interaction.

**Cas dangereux** : **utilisateurs humains** — un attaquant qui prend le compte
de l'user a `root` immédiatement. À éviter sauf raison technique précise.

## 📚 Exercice 4 — Limiter les commandes (moindre privilège)

```yaml
- name: Alice peut redemarrer chronyd uniquement
  community.general.sudoers:
    name: lab-rhce-alice-chronyd
    user: alice
    commands:
      - /usr/bin/systemctl restart chronyd
      - /usr/bin/systemctl status chronyd
    nopassword: true
    state: present
```

**Vérifiez** :

```bash
ssh ansible@db1.lab 'sudo cat /etc/sudoers.d/lab-rhce-alice-chronyd'
```

```text
alice ALL=(ALL) NOPASSWD:/usr/bin/systemctl restart chronyd, /usr/bin/systemctl status chronyd
```

🔍 **Observation** : alice peut **uniquement** lancer ces 2 commandes spécifiques
en sudo. `sudo systemctl restart sshd` → **refusé**.

**Pattern moindre privilège** : combiner avec un user dédié + clés SSH
restreintes (lab 42) → un développeur peut **uniquement** redémarrer son
service sans accès root complet.

## 📚 Exercice 5 — Règles sur un **groupe** plutôt qu'un user

```yaml
- name: Tous les membres d ops-team ont sudo
  community.general.sudoers:
    name: lab-rhce-ops-team
    group: ops-team   # Au lieu de "user:"
    commands: ALL
    state: present
```

**Vérifiez** :

```bash
ssh ansible@db1.lab 'sudo cat /etc/sudoers.d/lab-rhce-ops-team'
```

```text
%ops-team ALL=(ALL) ALL
```

🔍 **Observation** : le préfixe **`%`** désigne un groupe en syntaxe sudoers.
Tous les utilisateurs du groupe `ops-team` héritent des droits.

**Avantage** : ajouter un nouveau membre = `usermod -aG ops-team carl` →
automatiquement sudoer. Pas besoin de modifier le fichier sudoers.

## 📚 Exercice 6 — `runas:` (exécuter en tant que...)

Par défaut, `sudo` exécute en tant que `root`. `runas:` permet de **forcer un
autre utilisateur** comme cible.

```yaml
- name: Alice peut runner comme deploy uniquement
  community.general.sudoers:
    name: lab-rhce-alice-as-deploy
    user: alice
    runas: deploy
    commands: /opt/myapp/bin/deploy.sh
    nopassword: true
    state: present
```

**Vérifiez** :

```bash
ssh ansible@db1.lab 'sudo cat /etc/sudoers.d/lab-rhce-alice-as-deploy'
```

```text
alice ALL=(deploy) NOPASSWD:/opt/myapp/bin/deploy.sh
```

🔍 **Observation** : `(deploy)` impose que la commande soit exécutée **en tant
que `deploy`**, pas root. Alice peut faire `sudo -u deploy /opt/myapp/bin/deploy.sh`,
mais **pas** `sudo /opt/myapp/bin/deploy.sh` (qui tenterait root → refusé).

**Cas d'usage** : un opérateur peut redémarrer une app sous le user applicatif
**sans escalade root**.

## 📚 Exercice 7 — Suppression (`state: absent`)

```yaml
- name: Revoquer les droits sudo de bob
  community.general.sudoers:
    name: lab-rhce-bob-nopass
    state: absent
```

🔍 **Observation** : le **fichier** `/etc/sudoers.d/lab-rhce-bob-nopass` est
supprimé. Bob n'a plus de droits sudo.

**Important** : le module ne touche **que** au fichier qu'il a créé (`name:`
correspond au filename). Les autres fichiers `/etc/sudoers.d/*` ne sont pas
affectés.

## 📚 Exercice 8 — Le piège : `validate:` désactivé

```yaml
# ❌ DANGER
- community.general.sudoers:
    name: lab-rhce-broken
    user: alice
    commands: "INVALID SYNTAX !@#$"
    validation: absent   # Desactive visudo -cf
```

🔍 **Observation** : avec `validation: absent`, le module **ne valide pas** la
syntaxe. Le fichier est déposé tel quel. Si la syntaxe est invalide, sudo **se
casse globalement** (refuse de lire `/etc/sudoers.d/*`).

**Règle absolue** : **ne jamais désactiver `validation:`**. La validation est
gratuite (quelques ms) et empêche des incidents critiques.

## 🔍 Observations à noter

- **Module `community.general.sudoers:`** (pas builtin — collection requise).
- **Validation automatique** via `visudo -cf` — **toujours laisser activée**.
- **Pose les permissions correctes** automatiquement (`0440`).
- **`commands:`** pour le moindre privilège (commandes spécifiques uniquement).
- **`group:`** pour des règles sur un groupe (préfixe `%` en syntaxe sudoers).
- **`runas:`** pour exécuter en tant qu'un autre user (pas root par défaut).
- **`nopassword: true`** = sudo sans password — à réserver aux comptes
  techniques / CI.
- **Ne jamais** modifier `/etc/sudoers` directement — toujours `/etc/sudoers.d/*`.

## 🤔 Questions de réflexion

1. Vous voulez donner aux développeurs le droit de **redémarrer leur app** sans
   leur donner sudo complet. Combinez `commands:`, `runas:`, et `nopassword:`
   pour le scenario complet.

2. Pourquoi `/etc/sudoers.d/<file>` est-il **plus sûr** que `/etc/sudoers`
   directement ? (indice : isolation des règles, granularité, rollback).

3. Un collègue active `validation: absent` "parce que ça plante en CI sans
   accès root". Comment **vraiment** régler son problème (sans désactiver la
   validation) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **Pattern Defaults** : `Defaults env_keep += "ANSIBLE_*"` pour préserver des
  variables d'env Ansible. À gérer via `template:` sur `/etc/sudoers.d/defaults`.
- **`community.general.sudoers: noexec: true`** : empêche les programmes
  exécutés via sudo de lancer eux-mêmes des sub-shells.
- **Audit sudo** : `journalctl -u sudo` ou `/var/log/secure` (RHEL) tracent
  toutes les invocations sudo. Combiner avec `Defaults log_input,log_output`
  pour audit complet.
- **`!command`** dans `commands:` : **interdire** une commande même dans un `ALL`.
  Ex : `commands: ['ALL', '!/bin/rm -rf /']` (bien que cette syntaxe ait des
  limites — préférer une whitelist).
- **Lab 40 (`user:`) + Lab 42 (`authorized_key:`) + Lab 43 (`sudoers:`)** = la
  **trilogie d'onboarding** d'un membre d'équipe.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-utilisateurs/sudoers/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-utilisateurs/sudoers/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-utilisateurs/sudoers/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

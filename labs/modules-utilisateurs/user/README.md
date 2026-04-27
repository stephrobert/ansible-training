# Lab 40 — Module `user:` (créer, modifier, supprimer des utilisateurs)

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

🔗 [**Module user Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-user/)

`ansible.builtin.user:` gère les **utilisateurs Linux** : création, modification
des attributs (shell, home, groups), suppression, hashage de password,
gestion des clés SSH par défaut. C'est le module n°1 pour la **gestion de
comptes** sur les managed nodes.

Options critiques RHCE 2026 : **`name:`**, **`state:`**, **`shell:`**,
**`groups:`** + **`append:`**, **`password:`** (avec `password_hash`),
**`uid:`**, **`comment:`**.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Créer** un utilisateur avec home, shell, groupes secondaires.
2. **Hasher** un password avec `password_hash('sha512')` pour `password:`.
3. **Distinguer** `groups: + append: true` (ajouter) vs `groups:` seul (remplacer).
4. **Forcer** un `uid:` précis pour les comptes système.
5. **Supprimer** un compte avec `remove: true` (supprime aussi le home).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "for u in alice bob charlie deploy; do userdel -rf \$u 2>/dev/null; done; true"
```

## 📚 Exercice 1 — Création basique

Créez `lab.yml` :

```yaml
---
- name: Demo user simple
  hosts: db1.lab
  become: true
  tasks:
    - name: Creer alice
      ansible.builtin.user:
        name: alice
        comment: "Alice — admin RHCE 2026"
        shell: /bin/bash
        state: present

    - name: Verifier la creation
      ansible.builtin.command: id alice
      register: alice_id
      changed_when: false

    - name: Afficher l UID
      ansible.builtin.debug:
        var: alice_id.stdout
```

**Lancez** :

```bash
ansible-playbook labs/modules-utilisateurs/user/lab.yml
```

🔍 **Observation** :

- Premier run : `changed=1` — `useradd alice` exécuté.
- Deuxième run : `changed=0` — alice existe déjà avec les bons attributs.
- L'UID est **auto-attribué** (premier libre ≥ 1000).
- Le **home `/home/alice/`** est créé par défaut, le **groupe primaire `alice`**
  est créé automatiquement.

## 📚 Exercice 2 — Groupes secondaires : `append: true` vs sans

```yaml
- name: Creer bob avec wheel + docker (sans append)
  ansible.builtin.user:
    name: bob
    shell: /bin/bash
    groups: [wheel, docker]
    append: false  # Defaut

- name: Modifier bob — ajouter video (avec append)
  ansible.builtin.user:
    name: bob
    groups: [video]
    append: true   # Ajoute, sans toucher aux autres
```

**Vérifiez** :

```bash
ssh ansible@db1.lab 'id bob'
```

🔍 **Observation** : `bob` est dans `wheel`, `docker`, **et** `video`. Sans
`append: true`, la seconde tâche aurait **remplacé** les groupes — bob aurait
perdu `wheel` et `docker`.

**Règle absolue** : pour modifier les groupes d'un utilisateur existant, **toujours
`append: true`** sauf si vous voulez explicitement **réinitialiser** la liste.

## 📚 Exercice 3 — Password hashé

Cas critique : on ne **stocke jamais** un password en clair dans un playbook.

```yaml
- name: Creer charlie avec password
  ansible.builtin.user:
    name: charlie
    shell: /bin/bash
    password: "{{ 'PasswordEnClair2026' | password_hash('sha512') }}"
    update_password: on_create  # Ne change pas le password si l user existe deja
```

🔍 **Observation** :

- `password_hash('sha512')` génère un hash compatible `/etc/shadow`.
- **Sans salt fixe**, le hash diffère à chaque run → tâche **toujours `changed`**
  (perte d'idempotence).
- **`update_password: on_create`** = ne touche au password que **si l'user est
  créé** (pas s'il existe déjà). Permet la création initiale **sans** modifier
  le password à chaque run.

**Pattern propre RHCE** :

```yaml
# Stocker le hash dans host_vars (avec Vault)
# host_vars/db1.lab.yml :
charlie_password_hash: "$6$randomsalt$hashvalue..."

# Dans le playbook :
- ansible.builtin.user:
    name: charlie
    password: "{{ charlie_password_hash }}"
```

Le hash est généré **une fois** (`mkpasswd -m sha-512`) et stocké dans Vault.

## 📚 Exercice 4 — UID et GID forcés (comptes système)

Pour des comptes **système** ou **applicatifs**, on fixe souvent l'UID/GID pour
qu'ils soient **identiques sur tous les hôtes** (NFS, partage de fichiers).

```yaml
- name: Creer deploy avec UID 2000 (compte applicatif)
  ansible.builtin.user:
    name: deploy
    uid: 2000
    group: deploy   # Groupe primaire
    shell: /bin/bash
    home: /opt/deploy
    create_home: true
    system: false
```

🔍 **Observation** :

- **`uid: 2000`** force l'UID. Si l'UID est déjà pris par un autre user, la tâche
  **failed**.
- **`group:`** spécifie le groupe primaire (créé via le module `group:` séparé
  si nécessaire — voir lab 41).
- **`home:`** force le home (`/opt/deploy` au lieu de `/home/deploy`).
- **`system: true`** crée un user système (UID < 1000, pas de home par défaut).

## 📚 Exercice 5 — Modification d'un user existant

```yaml
- name: Modifier le shell de alice (zsh → bash)
  ansible.builtin.user:
    name: alice
    shell: /bin/zsh

- name: Verifier
  ansible.builtin.command: getent passwd alice
  register: alice_passwd
  changed_when: false

- ansible.builtin.debug:
    var: alice_passwd.stdout
    # → alice:x:1001:1001:...:/home/alice:/bin/zsh
```

🔍 **Observation** : le module **détecte** que le shell a changé et exécute
`usermod -s /bin/zsh alice`. Idempotent : 2e run → `ok`.

**Tous les attributs sont modifiables** : `comment`, `shell`, `home`, `groups`,
`uid`, `gid`. Sauf `name` (le name est la **clé** d'identification).

## 📚 Exercice 6 — Suppression (`state: absent`)

```yaml
- name: Supprimer charlie SANS son home
  ansible.builtin.user:
    name: charlie
    state: absent
    remove: false  # Defaut

- name: Supprimer alice ET son home
  ansible.builtin.user:
    name: alice
    state: absent
    remove: true
```

🔍 **Observation** :

- **`remove: false`** (défaut) = `userdel charlie` → home `/home/charlie/`
  **conserve**.
- **`remove: true`** = `userdel -r alice` → home + spool mail **supprimés**.

**Audit trail** : `remove: false` est le défaut **sécurisé** — vous pouvez
récupérer les fichiers d'un user supprimé. `remove: true` est pour le
**nettoyage final**.

## 📚 Exercice 7 — Le piège : `groups:` qui efface tout

```yaml
# ❌ DANGER : efface les groupes existants de bob
- ansible.builtin.user:
    name: bob
    groups: [wheel]
    # Pas de append: true → REMPLACE
```

🔍 **Observation** : si bob était déjà dans `[wheel, docker, video]`, après
cette tâche bob est **uniquement dans `wheel`**. Bob a perdu `docker` et
`video`.

**Mitigation** : **toujours** ajouter `append: true` lors de modification :

```yaml
- ansible.builtin.user:
    name: bob
    groups: [wheel]
    append: true  # ✅ Ajoute si pas deja dedans, ne retire rien
```

**Cas où `append: false` est légitime** : lorsque vous **réinitialisez**
intentionnellement la liste des groupes (offboarding, downgrade de droits).

## 🔍 Observations à noter

- **`name:`** = clé d'identification — ne **jamais** modifier.
- **`groups: + append: true`** pour AJOUTER aux groupes existants.
- **`password:`** = hash SHA-512 (utiliser `| password_hash('sha512')`).
- **`update_password: on_create`** pour ne pas écraser le password à chaque run.
- **`uid:`** forcé pour les comptes système / applicatifs (cohérence multi-hôtes).
- **`remove: true`** sur `state: absent` supprime aussi le home.
- **Idempotence** : tous les attributs sont vérifiés et ajustés si nécessaire.

## 🤔 Questions de réflexion

1. Vous voulez créer 50 utilisateurs avec leurs clés SSH respectives. Quel
   pattern (`loop:`, `subelements`, `with_items`) ? Comment articuler `user:`
   et `authorized_key:` (lab 42) ?

2. Pourquoi `password_hash('sha512')` **sans salt fixe** casse l'idempotence ?
   Quelle est la solution **propre** sans hash hardcodé dans le repo ?

3. Un collègue propose de **supprimer un user** avec `command: userdel -r`. Quels
   sont les **3 avantages** de `user: state: absent: remove: true` ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`generate_ssh_key: true`** : générer une paire SSH (privée+publique) au
  moment de la création du user. Pratique pour des comptes applicatifs.
- **`expires:`** : date d'expiration du compte (timestamp Unix). Utile pour
  des comptes temporaires (stagiaires, audit externe).
- **`password_lock: true`** : verrouiller le compte (`usermod -L`) sans le
  supprimer. Login via password désactivé, mais clés SSH fonctionnent encore.
- **Pattern `users +keys`** : combinaison `user:` + `authorized_key:` (lab 42)
  via `subelements`. Voir lab 21.
- **Module `getent:`** : récupérer les infos d'un user/group depuis NSS (LDAP,
  AD, NIS) sans dépendre de `/etc/passwd` local.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-utilisateurs/user/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-utilisateurs/user/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-utilisateurs/user/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

# Lab 41 — Module `group:` (gérer les groupes Linux)

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

🔗 [**Module group Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-group/)

`ansible.builtin.group:` gère les **groupes Linux** : création, suppression,
forçage du GID. Module compagnon de [`user:`](../40-modules-utilisateurs-user/) —
on crée d'abord les groupes, puis on rattache les utilisateurs.

Options principales : **`name:`**, **`state:`**, **`gid:`**, **`system: true`**
(pour les groupes système avec GID < 1000).

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Créer** un groupe simple et un groupe avec **GID forcé** (cohérence
   multi-hôtes).
2. **Distinguer** un groupe utilisateur (GID ≥ 1000) d'un groupe système
   (`system: true`, GID < 1000).
3. **Supprimer** un groupe avec `state: absent` (et son comportement quand des
   users en font encore partie).
4. **Ordonner** les tâches : créer le **groupe avant** l'utilisateur qui le
   référence.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "for g in dev-team ops-team rhce-shared; do groupdel \$g 2>/dev/null; done; true"
```

## 📚 Exercice 1 — Création basique

Créez `lab.yml` :

```yaml
---
- name: Demo group simple
  hosts: db1.lab
  become: true
  tasks:
    - name: Creer le groupe dev-team
      ansible.builtin.group:
        name: dev-team
        state: present

    - name: Verifier la creation
      ansible.builtin.command: getent group dev-team
      register: dev_team_check
      changed_when: false

    - name: Afficher l entree /etc/group
      ansible.builtin.debug:
        var: dev_team_check.stdout
        # → dev-team:x:1001:
```

**Lancez** :

```bash
ansible-playbook labs/modules-utilisateurs/group/lab.yml
```

🔍 **Observation** :

- 1er run : `changed=1` — `groupadd dev-team`.
- 2ème run : `changed=0` — déjà présent.
- Le **GID est auto-attribué** (premier libre ≥ 1000).

## 📚 Exercice 2 — GID forcé (cohérence multi-hôtes)

```yaml
- name: Creer ops-team avec GID 3000 force
  ansible.builtin.group:
    name: ops-team
    gid: 3000
    state: present

- name: Creer rhce-shared avec GID 3001 force
  ansible.builtin.group:
    name: rhce-shared
    gid: 3001
    state: present
```

🔍 **Observation** : sur 50 hôtes, ces groupes auront **toujours le même GID**.
C'est essentiel pour :

- **NFS** : si un fichier appartient à `gid=3001` côté serveur NFS, il faut que
  le client ait aussi `gid=3001` pour pouvoir l'ouvrir.
- **Containers** : volumes partagés entre hôte et conteneur.
- **Audit** : comparer les GIDs entre hôtes pour détecter une divergence.

**Si le GID est déjà pris** par un autre groupe : la tâche **failed**. Pas de
collision silencieuse.

## 📚 Exercice 3 — Groupe système (GID < 1000)

```yaml
- name: Creer un groupe systeme (GID auto < 1000)
  ansible.builtin.group:
    name: myapp-system
    system: true
    state: present
```

🔍 **Observation** : `system: true` indique à Ansible de **chercher un GID < 1000**
(par convention RHEL pour les groupes système). Sans `system:`, le GID
auto-attribué est ≥ 1000 (groupe utilisateur).

**Cas d'usage** : créer un groupe **applicatif** réservé au démon (nginx, postgres,
etc.) qui ne doit pas être confondu avec un groupe utilisateur.

## 📚 Exercice 4 — Suppression (`state: absent`)

```yaml
- name: Supprimer le groupe dev-team
  ansible.builtin.group:
    name: dev-team
    state: absent
```

**Avant la suppression**, créer un user qui utilise ce groupe :

```yaml
- name: Creer carl dans dev-team (avant la suppression)
  ansible.builtin.user:
    name: carl
    group: dev-team   # Groupe primaire
```

**Si vous tentez de supprimer un groupe qui est encore le groupe primaire** d'un
utilisateur, la tâche **failed** :

```text
groupdel: cannot remove the primary group of user 'carl'
```

🔍 **Observation** : protection système. Pour supprimer le groupe, il faut **d'abord
supprimer ou réassigner le user**.

```yaml
- name: Reassigner carl a un autre groupe primaire
  ansible.builtin.user:
    name: carl
    group: nogroup

- name: Maintenant on peut supprimer dev-team
  ansible.builtin.group:
    name: dev-team
    state: absent
```

## 📚 Exercice 5 — Ordonnancement : group AVANT user

Pattern classique : créer le **groupe** d'abord, **puis** les users qui le
référencent.

```yaml
- name: Step 1 — creer le groupe
  ansible.builtin.group:
    name: rhce-team
    gid: 5000
    state: present

- name: Step 2 — creer alice avec rhce-team comme primaire
  ansible.builtin.user:
    name: alice
    group: rhce-team   # Le groupe DOIT exister deja
    state: present
```

🔍 **Observation** : si vous inversez l'ordre, `user:` créerait alice avec un
groupe `rhce-team` **généré automatiquement** (GID auto-attribué). Puis quand
`group: gid: 5000` tente de le créer, **conflit** entre le GID demandé (5000)
et celui généré (1001 ou autre).

**Convention** : dans un même play, **toujours** ordonner :

1. `group:` (création des groupes)
2. `user:` (création des users qui les utilisent)
3. `authorized_key:` (clés SSH des users — voir lab 42)
4. `lineinfile:` ou autre (config sudo etc.)

## 📚 Exercice 6 — Le piège : modifier le GID d'un groupe existant

```yaml
- name: Tenter de changer le GID d ops-team
  ansible.builtin.group:
    name: ops-team
    gid: 3500   # Avant : 3000
```

🔍 **Observation** : la tâche **réussit** — `groupmod -g 3500 ops-team`. Mais
**tous les fichiers** appartenant à `gid=3000` sont **maintenant orphelins** :

```bash
# Avant changement
$ ls -la /home/alice/data
-rw-r--r-- 1 alice ops-team 0 ... data
$ stat -c '%g' /home/alice/data
3000  ← OK

# Apres changement
$ ls -la /home/alice/data
-rw-r--r-- 1 alice 3000     0 ... data   # Plus de nom !
```

**Solution** : ne **jamais** modifier un GID d'un groupe en production. Si
nécessaire :

1. Supprimer le groupe.
2. Recréer avec le nouveau GID.
3. **`chgrp -R`** sur tous les fichiers concernés.

## 🔍 Observations à noter

- **`name:`** = clé d'identification.
- **`gid:`** forcé pour la **cohérence multi-hôtes** (NFS, containers, audit).
- **`system: true`** = groupe avec GID < 1000 (convention RHEL).
- **Suppression d'un groupe primaire** d'un user → **failed**. Réassigner d'abord.
- **Ordonner** : `group:` AVANT `user:` qui le référence.
- **Ne pas modifier le GID** d'un groupe existant — fichiers orphelins.

## 🤔 Questions de réflexion

1. Vous avez 10 utilisateurs à créer dans `rhce-team`, plus 5 dans `dev-team`,
   plus 3 dans `ops-team`. Quel pattern (`loop:` sur `users` avec un champ
   `groups`, ou plays séparés) ?

2. Pourquoi `system: true` est-il important pour un groupe applicatif (`nginx`,
   `postgres`) ? Quel est le **risque concret** d'un groupe applicatif avec
   GID ≥ 1000 ?

3. Vous voulez **garantir** qu'un groupe a un GID précis sur 50 hôtes. Comment
   articulez-vous `group: gid:` avec `failed_when:` pour échouer si le GID
   diffère ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`local: true`** : forcer la création dans `/etc/group` même si le système
  utilise NIS/LDAP. Utile sur des hôtes intégrés à un annuaire mais qui doivent
  avoir des groupes locaux.
- **Module `getent:`** : récupérer les infos d'un groupe depuis NSS (LDAP, AD,
  NIS) sans dépendre de `/etc/group` local.
- **Pattern `groupinstall`** : pour des groupes liés à des paquets DNF
  (`@web-server`), c'est `dnf: name: '@web-server'` et pas `group:`.
- **Combinaison `group:` + `user:` + `authorized_key:`** : pattern d'inscription
  d'un nouveau membre dans une équipe — voir lab 42.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-utilisateurs/group/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-utilisateurs/group/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-utilisateurs/group/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

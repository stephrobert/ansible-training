# Lab 32 — Module `file:` (états, permissions, symlinks)

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

🔗 [**Module file Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-file/)

`ansible.builtin.file:` est le **couteau suisse des métadonnées de fichiers**.
Contrairement à `copy:`, il ne transfère **aucun contenu** — il agit uniquement
sur **l'existence**, le **mode**, le **propriétaire**, le **type** (fichier,
directory, symlink, hardlink). C'est le module idéal pour préparer une
**arborescence**, créer un **lien symbolique** vers la release courante, ou
**supprimer** un fichier obsolète.

`file:` se distingue par son option **`state:`** qui prend **6 valeurs** : `file`,
`directory`, `absent`, `link`, `hard`, `touch`. Maîtriser ces 6 états couvre 95%
des cas d'usage.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Distinguer** les 6 états : `file`, `directory`, `absent`, `link`, `hard`, `touch`.
2. **Créer** une arborescence multi-niveaux avec `state: directory`.
3. **Gérer** des liens symboliques (release courante, switching version).
4. **Propager** des permissions récursivement (`recurse: true`).
5. **Diagnostiquer** un symlink cassé (cible inexistante).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible web1.lab -m ping
ansible web1.lab -b -m shell -a "rm -rf /opt/myapp /etc/myapp-old.conf /var/log/myapp-init.timestamp /tmp/lab-file-*"
```

## 📚 Exercice 1 — Créer un répertoire (`state: directory`)

Créez `lab.yml` :

```yaml
---
- name: Demo file directory
  hosts: web1.lab
  become: true
  tasks:
    - name: Repertoire de logs applicatifs (avec parents)
      ansible.builtin.file:
        path: /var/log/myapp/archive
        state: directory
        owner: nobody
        group: nobody
        mode: "0750"
```

**Lancez** :

```bash
ansible-playbook labs/modules-fichiers/file/lab.yml
ssh ansible@web1.lab 'ls -la /var/log/myapp/'
```

🔍 **Observation** : `/var/log/myapp/` ET `/var/log/myapp/archive/` sont créés
**en une seule tâche**. Ansible crée automatiquement les parents (équivalent
`mkdir -p`).

**Idempotence** : 2e run → `changed=0` (déjà à l'état attendu).

**Modification** : changez `mode: "0750"` → `mode: "0700"`. Ansible **ajuste** le
mode sur les deux dossiers.

## 📚 Exercice 2 — Liens symboliques (pattern release)

Pattern classique de déploiement : `/opt/myapp/current` est un **symlink** vers
la release active.

```yaml
- name: Creer 2 dossiers de release
  ansible.builtin.file:
    path: "/opt/myapp/releases/{{ item }}"
    state: directory
    mode: "0755"
  loop: [v1.0.0, v1.1.0]

- name: Pointer current vers v1.0.0
  ansible.builtin.file:
    src: /opt/myapp/releases/v1.0.0
    dest: /opt/myapp/current
    state: link
    force: true

- name: Bascule vers v1.1.0 (mise a jour du symlink)
  ansible.builtin.file:
    src: /opt/myapp/releases/v1.1.0
    dest: /opt/myapp/current
    state: link
    force: true
```

🔍 **Observation** : à la 1ère exécution, `current` pointe vers `v1.0.0`. La 2e
tâche **bascule** le symlink vers `v1.1.0` (atomic via `rename`). Pattern classique
des **deployments blue/green** : préparer la nouvelle release dans `releases/`,
basculer `current` à la fin.

**`force: true`** est obligatoire si `current` existe déjà (en tant que fichier
ou symlink différent).

## 📚 Exercice 3 — Le piège du lien cassé

```yaml
- name: Creer un symlink vers une cible INEXISTANTE
  ansible.builtin.file:
    src: /opt/non-existent-target
    dest: /tmp/lab-file-broken-link
    state: link
    force: true
```

**Lancez et inspectez** :

```bash
ansible-playbook labs/modules-fichiers/file/lab.yml
ssh ansible@web1.lab 'ls -la /tmp/lab-file-broken-link'
```

🔍 **Observation** : le symlink est **créé** sans erreur Ansible, mais **pointe
vers le vide**. `ls -la` montre :

```text
lrwxrwxrwx 1 root root 27 ... lab-file-broken-link -> /opt/non-existent-target
```

Et `cat lab-file-broken-link` retourne `No such file or directory`.

**Solution** : vérifier la cible **avant** de créer le symlink :

```yaml
- name: Verifier que la cible existe
  ansible.builtin.stat:
    path: /opt/myapp/releases/v1.0.0
  register: target_check

- name: Creer symlink seulement si cible OK
  ansible.builtin.file:
    src: /opt/myapp/releases/v1.0.0
    dest: /opt/myapp/current
    state: link
    force: true
  when: target_check.stat.exists and target_check.stat.isdir
```

## 📚 Exercice 4 — Suppression (`state: absent`)

```yaml
- name: Nettoyer un fichier obsolete
  ansible.builtin.file:
    path: /etc/myapp-old.conf
    state: absent

- name: Nettoyer un dossier complet (RECURSIF)
  ansible.builtin.file:
    path: /tmp/lab-file-tobeRemoved
    state: absent
```

🔍 **Observation** :

- `state: absent` est **idempotent** : si déjà absent → `ok` (pas d'erreur).
- Sur un **dossier**, c'est **récursif** (équivalent `rm -rf`). **Attention !**
- Toujours **tester en `--check --diff`** avant `state: absent` sur un dossier
  en production.

**Pattern défensif** :

```yaml
- name: Stat avant suppression
  ansible.builtin.stat:
    path: /tmp/lab-file-tobeRemoved
  register: dir_stat

- name: Supprimer si existe (avec assertion)
  ansible.builtin.file:
    path: /tmp/lab-file-tobeRemoved
    state: absent
  when: dir_stat.stat.exists and dir_stat.stat.isdir
```

## 📚 Exercice 5 — `recurse: true` (propager mode/owner)

```yaml
- name: Reparer les permissions sur tout /var/log/myapp
  ansible.builtin.file:
    path: /var/log/myapp
    state: directory
    owner: nobody
    group: nobody
    mode: "0750"
    recurse: true
```

🔍 **Observation** : `recurse: true` propage `mode/owner/group` à **tous les
fichiers et sous-dossiers**. Pratique pour **réparer** des permissions cassées
ou homogénéiser une arborescence après un `cp -r` qui a tout mis en `root:root`.

**Performance** : `recurse: true` parcourt chaque inode → **lent sur de gros
volumes** (50K fichiers = 30+ secondes). Pour ces cas, préférer une commande
shell unique :

```yaml
- ansible.builtin.command: "chown -R nobody:nobody /var/log/myapp && chmod -R 0750 /var/log/myapp"
  changed_when: false  # ou un test plus fin
```

## 📚 Exercice 6 — `state: touch` (le seul non-idempotent)

```yaml
- name: Creer un timestamp d init
  ansible.builtin.file:
    path: /var/log/myapp-init.timestamp
    state: touch
    mode: "0644"
```

🔍 **Observation** : **`touch` est le seul état non-idempotent** — il modifie
**toujours le mtime**, donc `changed=1` à chaque run.

**Cas d'usage légitimes** :

- Timestamp d'init (créé une fois, mis à jour à chaque deploy).
- Healthcheck file (un cron qui vérifie le mtime < 5min).

**Cas où `touch` est un mauvais choix** : créer un fichier vide qu'on remplira
plus tard — préférer `copy: content: ""` qui est **idempotent**.

## 📚 Exercice 7 — Le piège : `state: file` ne crée pas le fichier

Contrairement à `state: directory` qui crée le dossier, **`state: file` ne crée
pas le fichier** s'il n'existe pas. C'est un état d'**affirmation** : "vérifier
que `path:` est bien un fichier (et ajuster les perms si oui)".

```yaml
# ❌ Ne marche PAS si /tmp/lab-file-test n existe pas
- ansible.builtin.file:
    path: /tmp/lab-file-test
    state: file
    mode: "0644"

# ✅ Pour creer un fichier vide
- ansible.builtin.file:
    path: /tmp/lab-file-test
    state: touch
    mode: "0644"

# ✅ Mieux : copy avec content vide (idempotent)
- ansible.builtin.copy:
    content: ""
    dest: /tmp/lab-file-test
    mode: "0644"
    force: false
```

🔍 **Observation** : `state: file` plante si le fichier n'existe pas. Pour créer
un fichier vide **idempotent**, utiliser `copy: content: "" force: false`.

## 🔍 Observations à noter

- **6 états** : `file` / `directory` / `absent` / `link` / `hard` / `touch`.
- **`directory` crée les parents** automatiquement (`mkdir -p`).
- **`absent` sur un dossier** est **récursif** — équivalent `rm -rf`, à utiliser avec précaution.
- **`link` ne vérifie pas** que la cible existe — symlink cassé silencieux.
- **`recurse: true`** propage mode/owner mais **lent** sur gros volumes.
- **`touch` est le seul non-idempotent** — toujours `changed=1`.
- **`state: file` ne crée pas** le fichier — utiliser `touch` ou `copy:`.

## 🤔 Questions de réflexion

1. Vous avez 50 000 fichiers dans `/var/log/myapp/` et vous voulez tous les
   passer en `mode 0640`. `file: recurse: true` ou `command: chmod -R` avec
   `changed_when:` ? Quels critères ?

2. Vous gérez un déploiement par releases (`/opt/myapp/releases/v1.0.0`,
   `v1.1.0`, etc.) avec un symlink `current`. Comment garantir une **bascule
   atomique** sans état intermédiaire visible aux utilisateurs ?

3. Pourquoi `state: touch` est-il **non-idempotent** par design, alors que tous
   les autres états le sont ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`modification_time:`** + **`access_time:`** : forcer un mtime/atime précis
  (au lieu du now de `touch`). Utile pour des cas de test ou de cache invalidation.
- **Hardlinks vs symlinks** : `state: hard` partage l'inode (le fichier sera
  effacé seulement quand TOUTES les références sont supprimées). Symlink = juste
  un pointeur.
- **Lab 31 (`copy:`)** : module compagnon — métadonnées **+** contenu en une
  tâche.
- **Lab 33 (`blockinfile:`)** : modifier un fichier existant sans le réécrire.
- **Module `ansible.posix.acl`** : pour gérer les ACL POSIX au-delà des
  permissions Unix de base.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-fichiers/file/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-fichiers/file/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-fichiers/file/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

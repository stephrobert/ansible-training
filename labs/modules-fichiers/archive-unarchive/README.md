# Lab 35 — Modules `archive:` et `unarchive:` (compresser et extraire)

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

🔗 [**Modules archive et unarchive Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/archive-unarchive/)

Deux modules complémentaires pour gérer des **tarballs** et **zips** :

- **`archive:`** crée une archive (`.tar.gz`, `.zip`, etc.) **sur le managed node**
  à partir d'un ou plusieurs chemins.
- **`unarchive:`** extrait une archive vers un dossier — depuis le control node
  (auto-copy), une URL, ou une archive déjà sur le managed node (`remote_src: true`).

Cas d'usage typiques : **backup avant migration** (archive d'un `/etc/myapp/`),
**déploiement applicatif** depuis un tarball stocké sur S3, **restauration** d'un
dump SQL compressé.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Créer** une archive `.tar.gz` sur le managed node avec `archive:`.
2. **Distinguer** les 3 modes de `unarchive:` (auto-copy, URL, `remote_src`).
3. **Rendre** `unarchive:` idempotent avec `creates:`.
4. **Identifier** le piège du **slash final** sur `archive: path:`.
5. **Utiliser** `extra_opts: --strip-components=1` pour les archives upstream.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -rf /opt/data-source /opt/backup /opt/restored"
```

## 📚 Exercice 1 — `archive:` simple

Créez `lab.yml` :

```yaml
---
- name: Demo archive
  hosts: db1.lab
  become: true
  tasks:
    - name: Repertoire source
      ansible.builtin.file:
        path: /opt/data-source
        state: directory
        mode: "0755"

    - name: Fichiers de donnees
      ansible.builtin.copy:
        content: "Donnee {{ item }}\n"
        dest: "/opt/data-source/file{{ item }}.txt"
        mode: "0644"
      loop: [1, 2, 3]

    - name: Repertoire pour l archive
      ansible.builtin.file:
        path: /opt/backup
        state: directory
        mode: "0755"

    - name: Creer l archive
      ansible.builtin.archive:
        path: /opt/data-source/
        dest: /opt/backup/data.tar.gz
        format: gz
```

**Lancez et inspectez** :

```bash
ansible-playbook labs/modules-fichiers/archive-unarchive/lab.yml
ssh ansible@db1.lab 'ls -la /opt/backup/ && tar tzf /opt/backup/data.tar.gz'
```

🔍 **Observation** : l'archive contient `file1.txt`, `file2.txt`, `file3.txt`
**au niveau racine** (pas dans `data-source/`). C'est l'effet du **slash final**
sur `path: /opt/data-source/`.

## 📚 Exercice 2 — Le piège du slash final

```yaml
- name: Sans slash final - inclut le dossier parent
  ansible.builtin.archive:
    path: /opt/data-source
    dest: /opt/backup/data-with-parent.tar.gz
    format: gz

- name: Avec slash final - inclut le contenu directement
  ansible.builtin.archive:
    path: /opt/data-source/
    dest: /opt/backup/data-flat.tar.gz
    format: gz
```

**Comparez** :

```bash
ssh ansible@db1.lab 'tar tzf /opt/backup/data-with-parent.tar.gz'
# data-source/file1.txt
# data-source/file2.txt
# data-source/file3.txt

ssh ansible@db1.lab 'tar tzf /opt/backup/data-flat.tar.gz'
# file1.txt
# file2.txt
# file3.txt
```

🔍 **Observation** : avec slash → contenu **plat**. Sans slash → contenu **sous le
dossier source**. Cela change la structure à l'extraction. **Toujours vérifier
avec `tar tzf`** avant de déployer.

## 📚 Exercice 3 — `unarchive:` mode auto-copy (`src:` local)

```yaml
- name: Repertoire pour extraction
  ansible.builtin.file:
    path: /opt/restored
    state: directory
    mode: "0755"

- name: Extraire (depuis archive sur le managed node, deja generee)
  ansible.builtin.unarchive:
    src: /opt/backup/data.tar.gz
    dest: /opt/restored
    remote_src: true
    creates: /opt/restored/file1.txt
```

🔍 **Observation** :

- **`remote_src: true`** : Ansible cherche `src:` côté managed node (pas côté control).
- **`creates: /opt/restored/file1.txt`** : si ce fichier existe → tâche **skipped**.
  Idempotence garantie.

**Lancer 2 fois** : 1ère fois `changed=1`, 2ème fois `ok` (skipped grâce à `creates:`).

## 📚 Exercice 4 — `unarchive:` mode URL distante

```yaml
- name: Telecharger et extraire (sans passer par le control node)
  ansible.builtin.unarchive:
    src: https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
    dest: /opt/
    remote_src: true
    creates: /opt/node_exporter-1.7.0.linux-amd64/node_exporter
    extra_opts:
      - "--strip-components=0"
```

🔍 **Observation** : Ansible **télécharge directement sur le managed node**
(pas de download sur le control node + transfer SSH). Plus efficace pour des
tarballs volumineux.

**`extra_opts: ["--strip-components=N"]`** : retire les N premiers niveaux de
l'arborescence. Astuce classique : convention `archive-X.Y.Z/...` upstream
→ `--strip-components=1` pour extraire directement dans `dest:` sans le dossier
parent.

## 📚 Exercice 5 — `unarchive:` mode classique (auto-copy depuis files/)

```yaml
- name: Extraire un tarball stocke localement (auto-copy)
  ansible.builtin.unarchive:
    src: files/myapp-1.0.tar.gz
    dest: /opt/myapp
    creates: /opt/myapp/bin/myapp
```

🔍 **Observation** : sans `remote_src: true`, Ansible **transfère** le tarball
depuis `files/` (côté control node) vers le managed node, puis l'extrait.

**Quand préférer cette approche** : tarballs versionnés dans le repo Ansible
(version contrôlée, pas de dépendance à internet).

**Différences entre les 3 modes** :

| Mode | Source | Transfert |
|---|---|---|
| auto-copy (défaut) | Control node (`files/`) | SSH vers managed |
| URL (`remote_src: true`) | URL HTTP(S) | Direct vers managed (sans control) |
| Local (`remote_src: true`) | Managed node | Pas de transfert (déjà là) |

## 📚 Exercice 6 — `archive:` avec exclusions

```yaml
- name: Archiver /var/log avec exclusions
  ansible.builtin.archive:
    path: /var/log
    dest: /opt/backup/logs.tar.gz
    format: gz
    exclude_path:
      - /var/log/journal
      - /var/log/btmp
      - /var/log/wtmp
```

🔍 **Observation** : `exclude_path:` accepte une liste de chemins à **exclure**
de l'archive. Pratique pour éviter d'embarquer des fichiers binaires de log
système ou des fichiers volumineux non utiles.

## 📚 Exercice 7 — Le piège : `creates:` sur le mauvais fichier

```yaml
# ❌ Mauvais : creates ne match jamais → extrait a chaque run
- ansible.builtin.unarchive:
    src: /opt/backup/data.tar.gz
    dest: /opt/restored
    remote_src: true
    creates: /opt/restored/binary-qui-n-existe-pas

# ✅ Bon : creates pointe vers un fichier reel apres extraction
- ansible.builtin.unarchive:
    src: /opt/backup/data.tar.gz
    dest: /opt/restored
    remote_src: true
    creates: /opt/restored/file1.txt
```

🔍 **Observation** : `creates:` doit pointer vers un **fichier qui existera
**après** l'extraction**. Si le fichier référencé n'apparaît jamais (pas dans
l'archive ou mauvais chemin), `unarchive:` extrait **à chaque run** → perte
d'idempotence.

**Bonne pratique** : utiliser un **fichier marqueur de version** (`/opt/myapp/VERSION`,
`/opt/myapp/.installed`) qui contient le numéro de version installé.

## 🔍 Observations à noter

- **`archive:`** crée des tarballs (`gz`, `bz2`, `xz`, `zip`).
- **`unarchive:`** a **3 modes** : auto-copy (défaut), URL (`remote_src: true`), local-au-managed (`remote_src: true`).
- **`creates:`** est obligatoire pour rendre `unarchive:` idempotent.
- **Slash final sur `archive: path:`** change la structure de l'archive — toujours `tar tzf` avant de déployer.
- **`extra_opts: ["--strip-components=1"]`** = pattern pour enlever le dossier racine d'une archive upstream.
- **`exclude_path:`** sur `archive:` pour éviter des fichiers volumineux ou non pertinents.

## 🤔 Questions de réflexion

1. Vous déployez node_exporter v1.7.0 depuis upstream. L'archive contient
   `node_exporter-1.7.0.linux-amd64/node_exporter`. Quel `--strip-components:` et
   quel `dest:` pour avoir `/opt/node_exporter/node_exporter` directement ?

2. Vous voulez **rapatrier** `/var/log` de db1 vers le control node. Quel
   pipeline : `archive:` + `fetch:`, ou directement `synchronize:` (rsync) ?

3. Pourquoi `creates:` doit-il référencer un **fichier précis** plutôt que
   `dest:` lui-même (qui existe toujours après le 1er run) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`archive: format: xz`** : compression plus efficace que `gz` (~30% de gain)
  mais plus lente. Pour des backups froids.
- **`archive: remove: true`** : supprime les sources après archivage. Pattern
  rotation logs : archiver puis supprimer le contenu original.
- **`unarchive: list_files: true`** : retourne la **liste des fichiers** dans
  `register:` sans extraire. Pour audit ou vérification préalable.
- **`synchronize:`** (collection ansible.posix) : rsync wrapper, alternative
  pour transferts massifs avec delta — pas idempotent par défaut, plus complexe.
- **Lab 31 (`copy:`)** + **Lab 34 (`fetch:`)** : modules de transfert simples
  (un fichier).

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-fichiers/archive-unarchive/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-fichiers/archive-unarchive/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-fichiers/archive-unarchive/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

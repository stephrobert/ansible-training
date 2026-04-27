# 🎯 Challenge — `archive` + `unarchive` (sauvegarder et restaurer)

## ✅ Objectif

Sur **db1.lab**, démontrer le pipeline complet :

1. **Préparer** : créer `/opt/data-source/` avec 3 fichiers
   `file1.txt`, `file2.txt`, `file3.txt` (contenu `Donnee 1`, `Donnee 2`, `Donnee 3`).
2. **Archiver** : produire `/opt/backup/data.tar.gz` (format `gz`) à partir
   du dossier source.
3. **Extraire** : restaurer l'archive dans `/opt/restored/`. **Idempotent**
   au 2e run grâce à `creates:`.

## 🧩 Modules clés

- `community.general.archive` (FQCN) — module **archive** (créer un .tar.gz, .zip, etc.).
- `ansible.builtin.unarchive` — extraction d'archive (livré avec `ansible-core`).

> ⚠️ Le module `archive` n'est **pas** dans `ansible.builtin` mais dans
> `community.general`. Si vous tapez `ansible.builtin.archive`, Ansible vous
> renverra une erreur "module not found".

## 🧩 Squelette

```yaml
---
- name: Challenge - archive + unarchive
  hosts: db1.lab
  become: true

  tasks:
    # Préparation
    - name: Répertoire source
      ansible.builtin.file:
        path: /opt/data-source
        state: directory
        mode: "0755"

    - name: Trois fichiers de données
      ansible.builtin.copy:
        content: "Donnee {{ item }}\n"
        dest: "/opt/data-source/file{{ item }}.txt"
        mode: "0644"
      loop: ???

    # Archivage
    - name: Répertoire de backup
      ansible.builtin.file:
        path: /opt/backup
        state: directory
        mode: "0755"

    - name: Archiver le dossier source
      community.general.archive:
        path: ???
        dest: ???
        format: ???

    # Extraction
    - name: Répertoire pour extraction
      ansible.builtin.file:
        path: /opt/restored
        state: directory
        mode: "0755"

    - name: Extraire l'archive (idempotent via creates)
      ansible.builtin.unarchive:
        src: ???
        dest: ???
        remote_src: ???       # l'archive est sur le managed node, pas sur le control
        creates: ???          # marqueur d'idempotence (le 2e run skippe)
```

> 💡 **`remote_src: true`** est crucial : sans ça, `unarchive` cherche
> l'archive **côté control node**, pas côté managed node, et plante.

**Pièges** :

> - **`creates:`** = marqueur d'idempotence. Sans, `unarchive` re-extrait
>   à chaque run → fichiers ré-écrits, mtime modifiés, `changed=1` à
>   chaque fois.
> - **`archive`** est dans **`community.general`**, pas `ansible.builtin`.
>   FQCN correct : `community.general.archive`.
> - **Format archive** : `unarchive` détecte `.tar.gz`, `.zip`, `.tar.bz2`
>   automatiquement. Pour des formats exotiques (`.7z`, `.xz`), passer
>   par `command: tar`.
> - **`extra_opts:`** : passer des flags au binaire tar. Ex
>   `--strip-components=1` pour retirer le 1er niveau de dossier.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-fichiers/archive-unarchive/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "ls -la /opt/data-source /opt/backup /opt/restored"
```

🔍 Au **2e run**, la tâche `unarchive` doit afficher `skipped` (preuve du
`creates:`).

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-fichiers/archive-unarchive/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/modules-fichiers/archive-unarchive clean
```

## 💡 Pour aller plus loin

- **`format: zip` / `format: bz2` / `format: xz`** : autres formats supportés.
- **`exclude_path:`** sur `archive` : exclure certains fichiers de l'archive
  (ex: `*.log`, `__pycache__/`).
- **Pattern backup horodaté** :

  ```yaml
  dest: "/opt/backup/data-{{ ansible_date_time.iso8601_basic_short }}.tar.gz"
  ```

  Crée une archive datée à chaque run — non idempotent par design (mais
  utile en cron pour avoir un historique).
- **Lint** :

   ```bash
   ansible-lint labs/modules-fichiers/archive-unarchive/challenge/solution.yml
   ```

# Préparer l'arborescence de release avant le premier déploiement

## La situation

L'équipe de dev livre **myapp** sur **web1.lab** jeudi et attend un système de
fichiers prêt : un répertoire de release versionné, un lien `current` que le
service lit, et un répertoire de logs dans lequel l'application écrit sans
tourner en root. La tentative manuelle précédente a laissé traîner un
`/etc/myapp-old.conf` que l'application charge encore. Vous préparez le terrain
depuis **control-node.lab**, dans un playbook qui sera rejoué à chaque release.

Votre mission :

1. Construire l'arborescence sur **web1.lab** : **`/opt/myapp/releases/v1.0.0`**
   (mode `0755`, root) et **`/opt/myapp/shared/logs`** (mode `0750`, propriété
   de `nobody`) pour que l'application écrive ses logs sans privilèges.
2. Faire pointer **`/opt/myapp/current`** vers la release `v1.0.0`, en
   **écrasant** un lien qui viserait déjà ailleurs.
3. Supprimer le résidu **`/etc/myapp-old.conf`** et poser le marqueur d'init
   **`/var/log/myapp-init.timestamp`** (mode `0644`).

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-file/

## 🎯 Challenge — Module `file:` (arborescence de release)

### ✅ Objectif

Sur **web1.lab**, construire une **arborescence type "release"** typique de
déploiement applicatif, en exerçant les **5 états** du module
`ansible.builtin.file`.

| Tâche | `state:` | Cible |
| --- | --- | --- |
| Répertoire de release | `directory` | `/opt/myapp/releases/v1.0.0` (mode 0755, owner root) |
| Répertoire de logs | `directory` | `/opt/myapp/shared/logs` (mode 0750, owner+group nobody) |
| Lien symbolique courant | `link` | `/opt/myapp/current` → `/opt/myapp/releases/v1.0.0` |
| Suppression d'une ancienne config | `absent` | `/etc/myapp-old.conf` (s'il existe) |
| Marqueur d'init | `touch` | `/var/log/myapp-init.timestamp` (mode 0644) |

### 🧩 Bloqué ?

```bash
dsoxlab hint modules-fichiers-file
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🧩 Squelette

```yaml
---
- name: Challenge - module file
  hosts: web1.lab
  become: true

  tasks:
    - name: Répertoire de release
      ansible.builtin.file:
        path: ???
        state: ???
        owner: root
        mode: "0755"

    - name: Répertoire de logs (owner nobody)
      ansible.builtin.file:
        path: ???
        state: ???
        owner: ???
        group: ???
        mode: "0750"

    - name: Symlink current → release
      ansible.builtin.file:
        src: ???
        dest: ???
        state: ???
        force: ???

    - name: Supprimer ancienne config
      ansible.builtin.file:
        path: ???
        state: ???

    - name: Marqueur d'init (touch)
      ansible.builtin.file:
        path: ???
        state: ???
        mode: "0644"
```

> 💡 **Pièges** :
>
> - **`state:`** = `directory`, `file`, `link`, `hard`, `touch`,
>   `absent`. Confusion classique : `file` ne crée pas le fichier
>   (utiliser `touch` pour créer, ou `copy:` pour poser un contenu).
> - **`recurse: true`** sur un répertoire applique mode/owner/group à
>   tout l'arbre. Attention aux performances sur gros volumes.
> - **`state: link`** + `src:` + `force: true`** : remplace un lien
>   existant. Sans `force`, modification refusée si le link existe déjà.
> - **`mode: u+x`** (symbolique) accepté en plus de `"0755"`. Utile pour
>   ajouter un bit sans écraser les autres.

### 🚀 Lancement

```bash
ansible-playbook labs/modules-fichiers/file/challenge/solution.yml
ansible web1.lab -m ansible.builtin.command -a "ls -la /opt/myapp/"
```

### 🧪 Validation automatisée

```bash
pytest -v labs/modules-fichiers/file/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean modules-fichiers-file
```

### 💡 Pour aller plus loin

- **`recurse: true`** : sur `state: directory`, applique `mode/owner/group` à
  toute l'arborescence (récursivement).
- **`hard:`** : crée un hard link (au lieu d'un symlink).
- **Pattern release blue/green** : posez **deux** symlinks (`current`, `next`)
  qui pointent vers deux releases différentes, et permutez-les
  atomiquement via `state: link, force: true`.
- **Lint** :

   ```bash
   ansible-lint labs/modules-fichiers/file/challenge/solution.yml
   ```

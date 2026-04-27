# Lab 52 — Module `find:` (recherche multi-fichiers)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```

## 🧠 Rappel

🔗 [**Module find Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-find/)

`ansible.builtin.find:` recherche **plusieurs fichiers** par pattern (glob ou regex),
âge, taille, type. C'est l'équivalent de la commande `find` Unix mais avec
résultat **structuré** (liste de dicts) consommable par `loop:` ensuite.

Là où `stat:` traite **un fichier**, `find:` en parcourt **plusieurs**. Cas
d'usage typiques RHCE 2026 : nettoyer les vieux logs (>7 jours), lister les
binaires setuid, supprimer les fichiers temporaires de plus de 100Mo.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Rechercher** par **pattern** (`patterns:` glob ou `use_regex: true`).
2. **Filtrer par âge** (`age: 7d`, `age_stamp: mtime`).
3. **Filtrer par taille** (`size: +100m`).
4. **Filtrer par type** (`file_type: file/directory/link`).
5. **Combiner** `find:` + `loop: + file: state: absent` pour un cleanup ciblé.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -rf /tmp/lab-find-test; mkdir -p /tmp/lab-find-test"
```

## 📚 Exercice 1 — Setup : créer des fichiers de test

```yaml
---
- name: Setup find test
  hosts: db1.lab
  become: true
  tasks:
    - name: Creer 5 fichiers .log de tailles diverses
      ansible.builtin.shell: |
        cd /tmp/lab-find-test
        for n in 1 2 3 4 5; do
          dd if=/dev/zero of=app${n}.log bs=1M count=$((n * 5)) 2>/dev/null
        done
        ls -la /tmp/lab-find-test/
      register: setup_output

    - name: Afficher
      ansible.builtin.debug:
        var: setup_output.stdout_lines
```

🔍 **Observation** : 5 fichiers `app1.log` (5M) à `app5.log` (25M).

## 📚 Exercice 2 — Recherche par pattern (glob)

```yaml
- name: Trouver tous les .log
  ansible.builtin.find:
    paths: /tmp/lab-find-test
    patterns: '*.log'
  register: log_files

- name: Afficher la liste
  ansible.builtin.debug:
    msg: "{{ log_files.files | map(attribute='path') | list }}"
```

🔍 **Observation** : `log_files.files` est une **liste de dicts** (un par fichier
trouvé) avec : `path`, `size`, `mode`, `mtime`, `uid`, `gid`, etc. — comme un
`stat:` par fichier.

**Champs utiles du registre** :

- **`log_files.files`** : liste des fichiers trouvés (dicts).
- **`log_files.matched`** : nombre total trouvé.
- **`log_files.examined`** : nombre de fichiers parcourus avant filtrage.

## 📚 Exercice 3 — Filtrer par taille

```yaml
- name: Trouver les .log de plus de 10Mo
  ansible.builtin.find:
    paths: /tmp/lab-find-test
    patterns: '*.log'
    size: 10m
  register: big_logs

- name: Afficher
  ansible.builtin.debug:
    msg: "Gros logs : {{ big_logs.files | map(attribute='path') | list }}"
    # → app3.log (15M), app4.log (20M), app5.log (25M)
```

**Format `size:`** :

- **`10m`** = au moins 10 mégaoctets (sans préfixe = `>= 10m`).
- **`-100k`** = moins de 100 kilooctets (préfixe `-` uniquement).
- **`1g`** = au moins 1 gigaoctet.
- Suffixes : `b` (bytes), `k`, `m`, `g`, `t`.

> ⚠️ **Pas de préfixe `+`** comme avec la commande `find` Unix — Ansible
> rejette `+10m`. Sans préfixe = supérieur ou égal.

## 📚 Exercice 4 — Filtrer par âge

```yaml
- name: Trouver les fichiers modifies depuis plus de 7 jours
  ansible.builtin.find:
    paths: /var/log
    patterns: '*.log'
    age: 7d
  register: old_logs

- name: Trouver les fichiers tres recents (< 1h)
  ansible.builtin.find:
    paths: /var/log
    patterns: '*.log'
    age: -1h
  register: recent_logs
```

**Format `age:`** :

- **`7d`** = 7 jours ou plus (par défaut basé sur `mtime`).
- **`-1h`** = moins d'1 heure (signe `-` = inférieur).
- Suffixes : `s` (secondes), `m` (minutes), `h` (heures), `d` (jours), `w` (semaines).

**`age_stamp:`** : choisir le timestamp à comparer.

- **`mtime`** (défaut) : dernière modification.
- **`atime`** : dernier accès.
- **`ctime`** : dernier changement de métadonnée.

## 📚 Exercice 5 — Filtrer par type

```yaml
- name: Trouver tous les dossiers
  ansible.builtin.find:
    paths: /tmp/lab-find-test
    file_type: directory
  register: dirs

- name: Trouver les symlinks
  ansible.builtin.find:
    paths: /etc
    file_type: link
    recurse: false
  register: symlinks
```

**Valeurs `file_type:`** : `file` (défaut), `directory`, `link`, `any`.

## 📚 Exercice 6 — `recurse: true` (descente récursive)

```yaml
- name: Trouver TOUS les .conf dans /etc et sous-dossiers
  ansible.builtin.find:
    paths: /etc
    patterns: '*.conf'
    recurse: true
  register: all_conf

- name: Compter
  ansible.builtin.debug:
    msg: "{{ all_conf.matched }} fichiers .conf trouves dans /etc/"
```

🔍 **Observation** : sans `recurse: true`, `find:` ne regarde que **`/etc/*.conf`**.
Avec, il descend dans `/etc/sysconfig/`, `/etc/sysctl.d/`, etc.

**Performance** : `recurse: true` sur `/` peut prendre des heures sur un système
chargé. **Toujours** scoper avec `paths:` précis.

## 📚 Exercice 7 — `find:` + cleanup automatique

Pattern classique : **supprimer** tous les fichiers matching un pattern.

```yaml
- name: Trouver les .log > 1Mo et plus de 0 jours
  ansible.builtin.find:
    paths: /tmp/lab-find-test
    patterns: '*.log'
    size: +1m
  register: logs_to_clean

- name: Supprimer ces fichiers
  ansible.builtin.file:
    path: "{{ item.path }}"
    state: absent
  loop: "{{ logs_to_clean.files }}"
  loop_control:
    label: "{{ item.path }}"
```

🔍 **Observation** : pattern `find` + `loop: + file: state: absent`. Idempotent
(un 2e run trouve 0 fichier → `loop:` 0 itération).

**Alternative shell** : `find /tmp/lab-find-test -name '*.log' -size +1M -delete`.
Moins lisible, moins idempotent, mais plus rapide sur **gros volumes**.

## 📚 Exercice 8 — Le piège : `find:` sur une partition NFS lente

```yaml
- name: Find sur NFS (lent)
  ansible.builtin.find:
    paths: /mnt/nfs-data
    patterns: '*.dump'
    recurse: true
  register: nfs_dumps
  timeout: 60   # Tuer apres 60s
```

🔍 **Observation** : sur un NFS lent ou un FS très grand, `find:` peut bloquer
le play. **`timeout:`** au niveau task limite la durée.

**Mitigation** :

- **Scoper** par sous-dossier précis (pas `/`).
- **Limiter** la profondeur via `depth:` (Ansible 2.10+, sinon shell).

## 🔍 Observations à noter

- **`find:`** retourne `<reg>.files` (liste de dicts) + `<reg>.matched` (count).
- **`patterns:`** = glob par défaut, `use_regex: true` pour regex Python.
- **`size: +10m`** / **`age: 7d`** = filtres standards.
- **`recurse: true`** = descente récursive (attention performance).
- **`file_type:`** : `file` / `directory` / `link` / `any`.
- **Pattern `find + loop + file: state: absent`** = cleanup idempotent.

## 🤔 Questions de réflexion

1. Vous voulez **archiver** tous les `.log` de plus de 7 jours dans
   `/var/backups/` avant de les supprimer. Pipeline complet (modules + ordre) ?

2. Différence entre `patterns: '*.log'` (glob) et `patterns: '\\.log$'` avec
   `use_regex: true` ?

3. Sur 100 hôtes, `find:` recursif sur `/var/log/` prend 30s par hôte. Comment
   **paralléliser** sans saturer ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`get_checksum: true`** : calcule le hash de chaque fichier trouvé. Lent
  mais utile pour audit.
- **`hidden: true`** : inclut les fichiers `.<dotfile>`. Désactivé par défaut.
- **`excludes:`** : liste de patterns à **exclure** du résultat.
- **`depth:`** : profondeur maximale (Ansible 2.10+) — utile sur arborescences
  profondes.
- **Lab 51 (`stat:`)** = stat sur **un** fichier ; **Lab 52 (`find:`)** = sur
  plusieurs.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/modules-diagnostic/find/lab.yml
ansible-lint labs/modules-diagnostic/find/challenge/solution.yml
ansible-lint --profile production labs/modules-diagnostic/find/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

# 🎯 Challenge — `stat:` pour audit de fichiers système

## ✅ Objectif

Sur **db1.lab**, utiliser `ansible.builtin.stat` pour collecter des **infos**
sur 3 fichiers système, puis les écrire dans un rapport `/tmp/lab-stat-report.txt`.

| Fichier | Info à collecter |
| --- | --- |
| `/etc/passwd` | existe + mode + checksum SHA256 |
| `/etc/shadow` | existe + mode + uid (doit être 0 = root) |
| `/etc/sudoers` | existe + mode (doit être 0440) |

Le rapport doit être un fichier `.txt` lisible avec les 3 entrées.

## 🧩 Étapes

1. **3 tâches `stat:`** parallèles (avec `get_checksum: true` pour le 1er).
2. **`copy: content:`** qui assemble un rapport multi-ligne via Jinja2.

## 🧩 Squelette

```yaml
---
- name: Challenge - stat audit
  hosts: db1.lab
  become: true

  tasks:
    - name: Stat /etc/passwd avec checksum SHA256
      ansible.builtin.stat:
        path: ???
        get_checksum: ???
        checksum_algorithm: ???
      register: passwd_stat

    - name: Stat /etc/shadow
      ansible.builtin.stat:
        path: ???
      register: shadow_stat

    - name: Stat /etc/sudoers
      ansible.builtin.stat:
        path: ???
      register: sudoers_stat

    - name: Generer le rapport
      ansible.builtin.copy:
        content: |
          /etc/passwd
            exists: {{ ??? }}
            mode: {{ ??? }}
            sha256: {{ ??? }}

          /etc/shadow
            exists: {{ ??? }}
            mode: {{ ??? }}
            uid: {{ ??? }}

          /etc/sudoers
            exists: {{ ??? }}
            mode: {{ ??? }}
        dest: ???
        mode: "0644"
```

> 💡 **Pièges** :
>
> - **`stat:` ne crée rien**, c'est lecture seule. Toujours
>   `changed_when: false` n'est pas nécessaire car le module est
>   nativement read-only.
> - **`<var>.stat.exists`** : `true` si le path existe (fichier OU
>   répertoire OU lien). Pour distinguer : `<var>.stat.isdir`,
>   `<var>.stat.islnk`.
> - **`<var>.stat.mode`** : string en octal (ex `"0644"`). Pas un int.
>   Comparer avec `'0644'` entre guillemets.
> - **`get_checksum: true`** : ajoute `<var>.stat.checksum` (sha1 par
>   défaut). Coûteux sur gros fichiers — désactivé par défaut.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-diagnostic/stat/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/lab-stat-report.txt"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-diagnostic/stat/challenge/tests/
```

## 🧹 Reset

```bash
ansible db1.lab -b -m file -a "path=/tmp/lab-stat-report.txt state=absent"
```

## 💡 Pour aller plus loin

- **`get_attributes: true`** : ajouter les attributs étendus (xattrs,
  contextes SELinux) au rapport — utile pour les audits sécurité poussés.
- **`get_mime: true`** : ajouter le type MIME — pratique pour distinguer
  un binaire d'un script texte.
- **`follow: true`** : suivre les symlinks. Désactivé par défaut.
- **Pattern audit** : combiner `stat:` × N fichiers + `template:` pour générer
  un **rapport HTML** des permissions critiques.
- **Lint** :

   ```bash
   ansible-lint labs/modules-diagnostic/stat/challenge/solution.yml
   ```

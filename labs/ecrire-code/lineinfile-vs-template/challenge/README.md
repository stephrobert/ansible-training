# 🎯 Challenge — `lineinfile` vs `template` (les 2 approches)

## ✅ Objectif

Sur **db1.lab**, démontrer **deux philosophies opposées** pour gérer un
fichier de configuration :

- **`lineinfile`** = **chirurgical**, on touche **une ligne** sans réécrire le
  reste du fichier (idéal pour `/etc/hosts`, `/etc/sysctl.conf`, etc.).
- **`template`** = **propriétaire complet**, on **réécrit** tout le fichier
  depuis un template Jinja2 (idéal pour les configs qu'on génère
  intégralement, comme `/etc/nginx/nginx.conf` métier).

## 🧩 Tâche 1 — `lineinfile` sur `/etc/hosts`

Ajoutez une **seule ligne** dans `/etc/hosts` :

```text
192.168.99.99 mon-host.lab
```

Sans toucher aux autres lignes existantes.

Indices :

- `path:` → fichier à modifier.
- `line:` → contenu de la ligne.
- `regexp:` → pour rendre l'opération idempotente : si une ligne matchant le
  motif existe déjà, elle est **remplacée** (pas dupliquée).
- `state: present` (défaut).

## 🧩 Tâche 2 — `template` sur `/etc/myapp.conf`

Créez `challenge/templates/myapp.conf.j2` qui produit :

```ini
[server]
host = 0.0.0.0
port = 8080
workers = 4

[database]
url = postgres://db1.lab/myapp
pool_size = 10
```

Variables source (à mettre dans `vars:` du play) :

```yaml
server:
  host: "0.0.0.0"
  port: 8080
  workers: 4
database:
  url: "postgres://db1.lab/myapp"
  pool_size: 10
```

Le template doit interpoler **chaque** valeur depuis ces dicts (ex:
`{{ server.host }}`, `{{ database.pool_size }}`).

## 🧩 Squelette

```yaml
---
- name: "Challenge - lineinfile vs template"
  hosts: db1.lab
  become: true

  vars:
    server:
      # ...
    database:
      # ...

  tasks:
    - name: Ajouter une entrée DNS via lineinfile
      ansible.builtin.lineinfile:
        path: ???
        regexp: ???
        line: ???
        state: present

    - name: Générer /etc/myapp.conf depuis le template
      ansible.builtin.template:
        src: ???
        dest: ???
        mode: "0644"
```

> 💡 **Pièges** :
>
> - **`lineinfile`** = modifier **une ligne** dans un fichier existant
>   (ex: `/etc/hosts`, `/etc/sshd_config`). Si la ligne n'est pas
>   matchée par `regexp:`, elle est **ajoutée** à la fin.
> - **`template`** = remplacer **tout le fichier**. Idempotent par
>   checksum, donc pas de drift.
> - **Quand préférer `lineinfile`** : modifier 1-3 lignes dans un fichier
>   géré par un paquet (ne pas écraser les valeurs par défaut).
> - **Quand préférer `template`** : on possède le fichier en entier
>   (config app maison, motd, banner). Plus lisible et auditable.
> - **`blockinfile`** (lab 33) : entre les deux — gère un **bloc
>   marqué** dans un fichier existant.

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/lineinfile-vs-template/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "grep mon-host /etc/hosts"
ansible db1.lab -m ansible.builtin.command -a "cat /etc/myapp.conf"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/lineinfile-vs-template/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ecrire-code/lineinfile-vs-template clean
```

## 💡 Pour aller plus loin

- **Quand utiliser `lineinfile` vs `template` ?**
  - **`lineinfile`** : config gérée par plusieurs sources (Ansible + autre
    outil + admin), ou config par défaut qu'on ne maîtrise pas (ex:
    `/etc/sshd_config` livré par le paquet).
  - **`template`** : config 100 % gérée par Ansible (pas d'autre source de
    vérité). Plus prévisible, plus testable.
- **`blockinfile`** (lab 33) : entre les deux. Gère un **bloc** délimité par
  des markers. Idéal quand on veut ajouter une section sans toucher au reste.
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/lineinfile-vs-template/challenge/solution.yml
   ```

# 🎯 Challenge — Module `copy:` (déployer un banner SSH)

## ✅ Objectif

Sur **web1.lab**, déposer **deux fichiers** dans `/etc/` :

1. `/etc/ssh/banner-rhce` — depuis un fichier source local
   (`challenge/files/banner-ssh.txt`), avec **backup activé**.
2. `/etc/motd-rhce` — depuis un **contenu inline** (`content:`).

Démontre la différence `src:` (fichier source) vs `content:` (string).

## 🧩 Fichiers à créer

### 1) `challenge/files/banner-ssh.txt`

À créer côté control node. Contenu :

```text
=====================================
   Acces autorise uniquement
   Toute connexion est tracee
=====================================
```

### 2) `challenge/solution.yml`

Squelette :

```yaml
---
- name: Challenge - module copy (src + content)
  hosts: web1.lab
  become: true

  tasks:
    - name: Déployer le banner SSH (depuis un fichier local)
      ansible.builtin.copy:
        src: ???
        dest: ???
        owner: root
        group: root
        mode: "0644"
        backup: ???

    - name: Marquer le serveur via content inline
      ansible.builtin.copy:
        content: ???
        dest: ???
        owner: root
        group: root
        mode: "0644"
```

## 🧩 Sortie attendue

| Fichier | Source | Contenu |
| --- | --- | --- |
| `/etc/ssh/banner-rhce` | `files/banner-ssh.txt` | les 4 lignes du banner |
| `/etc/motd-rhce` | inline | `Serveur RHCE — gere par Ansible` |

> 💡 **Pièges** :
>
> - **`src:` vs `content:`** : `src:` push un fichier local du control
>   node ; `content:` pose une chaîne directement. Mutuellement exclusifs.
> - **Chemin `src:`** relatif au `<role>/files/` ou au `files/` à côté du
>   playbook. Pas besoin du préfixe `files/` si le fichier est dans
>   `<role>/files/`.
> - **`backup: true`** crée une copie horodatée avant écraser. Précieux
>   pour les fichiers partagés (`/etc/ssh/*`).
> - **Mode toujours quoté** : `"0644"`, pas `0644` (octal mal interprété).
> - **`copy:` est idempotent par checksum** — au 2ᵉ run identique,
>   `changed=0`.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-fichiers/copy/challenge/solution.yml
ansible web1.lab -m ansible.builtin.command -a "cat /etc/ssh/banner-rhce"
ansible web1.lab -m ansible.builtin.command -a "cat /etc/motd-rhce"
```

🔍 Au 2e run après modif du fichier source, vous verrez
`/etc/ssh/banner-rhce.<timestamp>~` apparaître (preuve de `backup: true`).

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-fichiers/copy/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/modules-fichiers/copy clean
```

## 💡 Pour aller plus loin

- **`force: false`** : n'écrase pas le fichier s'il existe déjà (utile pour
  une config initiale qu'on ne veut pas remettre à zéro).
- **`remote_src: true`** : le `src:` est sur le **managed node** (pas sur le
  control node). Permet de copier un fichier d'un endroit à un autre côté
  serveur.
- **`validate:`** : valide le fichier avant écrasement (ex: `validate: 'sshd
  -t -f %s'` pour `sshd_config`). Si la validation échoue, le fichier
  d'origine reste intact.
- **Lint** :

   ```bash
   ansible-lint labs/modules-fichiers/copy/challenge/solution.yml
   ```

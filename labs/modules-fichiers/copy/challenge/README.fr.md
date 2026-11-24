# Déployer la bannière légale sur le tier web

## La situation

L'audit de sécurité s'est terminé sur un constat bloquant : **web1.lab** ouvre
les sessions SSH sans le moindre avertissement légal, alors que la conformité
exige la preuve que l'accès est annoncé comme tracé avant même le shell. Le
même audit demande que chaque hôte s'identifie dans son message du jour. Vous
travaillez depuis **control-node.lab** : rien ne se tape à la main sur le
serveur, la bannière part en playbook pour que les vingt serveurs suivants ne
coûtent qu'un `--limit`.

Votre mission :

1. Pousser le texte de la bannière légale depuis le control node vers
   **`/etc/ssh/banner-rhce`** sur **web1.lab**, propriété de root, lisible par
   tous, avec **sauvegarde** de la version précédente.
2. Écrire le marqueur d'identité du serveur directement dans
   **`/etc/motd-rhce`** en **contenu inline**, sans embarquer un fichier source
   pour trois mots.
3. Garder les deux tâches **idempotentes** : un second passage doit annoncer
   zéro changement.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-copy/

## 🎯 Challenge — Module `copy:` (déployer un banner SSH)

### ✅ Objectif

Sur **web1.lab**, déposer **deux fichiers** dans `/etc/` :

1. `/etc/ssh/banner-rhce` — depuis un fichier source local
   (`challenge/files/banner-ssh.txt`). Ajouter `backup: true` est une
   **bonne pratique de production**, recommandée mais **non vérifiée par les
   tests** (un premier passage n'a rien à sauvegarder).
2. `/etc/motd-rhce` — depuis un **contenu inline** (`content:`).

Démontre la différence `src:` (fichier source) vs `content:` (string).

### 🧩 Fichiers à créer

#### 1) `challenge/files/banner-ssh.txt`

À créer côté control node. Contenu :

```text
=====================================
   Acces autorise uniquement
   Toute connexion est tracee
=====================================
```

#### 2) `challenge/solution.yml`

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
        backup: true              # bonne pratique (prod), non vérifiée par les tests

    - name: Marquer le serveur via content inline
      ansible.builtin.copy:
        content: ???
        dest: ???
        owner: root
        group: root
        mode: "0644"
```

### 🧩 Sortie attendue

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
> - **`backup: true`** crée une copie horodatée avant écraser. Bonne pratique
>   de production pour les fichiers partagés (`/etc/ssh/*`), **non vérifiée par
>   les tests** (rien à sauvegarder au premier passage).
> - **Mode toujours quoté** : `"0644"`, pas `0644` (octal mal interprété).
> - **`copy:` est idempotent par checksum** — au 2ᵉ run identique,
>   `changed=0`.

### 🚀 Lancement

```bash
ansible-playbook labs/modules-fichiers/copy/challenge/solution.yml
ansible web1.lab -m ansible.builtin.command -a "cat /etc/ssh/banner-rhce"
ansible web1.lab -m ansible.builtin.command -a "cat /etc/motd-rhce"
```

🔍 Au 2e run après modif du fichier source, vous verrez
`/etc/ssh/banner-rhce.<timestamp>~` apparaître (preuve de `backup: true`).

### 🧪 Validation automatisée

```bash
pytest -v labs/modules-fichiers/copy/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean modules-fichiers-copy
```

### 💡 Pour aller plus loin

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

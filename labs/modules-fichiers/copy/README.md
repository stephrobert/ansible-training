# Lab 31 — Module `copy:` (transfert et contenu inline)

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

🔗 [**Module copy Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-copy/)

`ansible.builtin.copy:` est le module de **transfert** par excellence. Il pousse
un fichier du **control node** vers le **managed node**, ou écrit un **contenu
inline** via `content:`. Différence clé avec `template:` : `copy:` transfère
**tel quel**, pas d'interpolation Jinja2.

Options critiques pour la production : **`mode:`**, **`owner:`**, **`group:`**,
**`backup: true`**, **`validate:`**, et le piège du `content:` non terminé par `\n`.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Distinguer** `src:` (fichier local) et `content:` (inline) — quand utiliser lequel.
2. **Maîtriser** les options `mode`, `owner`, `group`, `backup`, `force`, `validate`.
3. **Identifier** le piège du `content:` sans `\n` final.
4. **Éviter** le piège YAML sur `mode:` non quoté.
5. **Choisir** entre `copy:` et `template:` selon que le fichier a besoin d'interpolation.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible web1.lab -m ping
mkdir -p labs/modules-fichiers/copy/files
ansible web1.lab -b -m shell -a "rm -f /etc/issue.net.* /tmp/lab-copy-*.txt /etc/motd-rhce*"
```

## 📚 Exercice 1 — Transfert d'un fichier local (`src:`)

Créez `files/banner.txt` :

```text
=====================================
   Acces autorise uniquement
   Toute connexion est tracee
=====================================
```

Créez `lab.yml` :

```yaml
---
- name: Demo copy src
  hosts: web1.lab
  become: true
  tasks:
    - name: Deployer le banner SSH
      ansible.builtin.copy:
        src: files/banner.txt
        dest: /etc/ssh/banner-rhce
        owner: root
        group: root
        mode: "0644"
        backup: true
```

**Lancez** :

```bash
ansible-playbook labs/modules-fichiers/copy/lab.yml
ssh ansible@web1.lab 'sudo cat /etc/ssh/banner-rhce && ls -la /etc/ssh/banner-rhce*'
```

🔍 **Observation** :

- Premier run : `changed=1`, fichier créé.
- Deuxième run : `changed=0` (idempotent — checksum SHA1 identique).
- **Si vous modifiez `files/banner.txt`** et relancez : `changed=1`, et un fichier
  `banner-rhce.<timestamp>~` apparaît (backup).

## 📚 Exercice 2 — Contenu inline (`content:`)

```yaml
- name: Marquer le serveur via content inline
  ansible.builtin.copy:
    content: "Serveur RHCE — provisionne le {{ ansible_date_time.iso8601 }}\n"
    dest: /etc/motd-rhce
    owner: root
    group: root
    mode: "0644"
```

🔍 **Observation** :

- Pas besoin de créer un fichier source — `content:` injecte la string directement.
- Le **`\n` final** est crucial : sans lui, `cat /etc/motd-rhce` colle la sortie
  au prompt suivant.
- À chaque run, `ansible_date_time.iso8601` change → tâche **toujours `changed`**
  (perte d'idempotence). À éviter sauf intention explicite.

## 📚 Exercice 3 — Le piège du `\n` manquant

```yaml
- name: Mauvais (pas de \n final)
  ansible.builtin.copy:
    content: "ligne sans newline"
    dest: /tmp/lab-copy-no-newline.txt

- name: Bon (avec \n)
  ansible.builtin.copy:
    content: "ligne avec newline\n"
    dest: /tmp/lab-copy-with-newline.txt
```

**Lancez et inspectez** :

```bash
ansible-playbook labs/modules-fichiers/copy/lab.yml
ssh ansible@web1.lab 'cat -A /tmp/lab-copy-no-newline.txt'
ssh ansible@web1.lab 'cat -A /tmp/lab-copy-with-newline.txt'
```

🔍 **Observation** :

- Sans `\n` : `cat -A` montre `ligne sans newline` (sans `$` final). Le shell
  affichera `ligne sans newlineansible@web1$` (collé au prompt).
- Avec `\n` : `cat -A` montre `ligne avec newline$` — proprement terminé.

**Certains parseurs** (cron, systemd, openrc) **refusent** les fichiers sans `\n`
final. Toujours terminer `content:` par `\n`.

## 📚 Exercice 4 — `validate:` (rejeter une config invalide)

Pattern critique pour `sshd_config`, `nginx.conf`, `sudoers`.

```yaml
- name: Deployer sshd_config (avec validation)
  ansible.builtin.copy:
    src: files/sshd_config
    dest: /etc/ssh/sshd_config
    mode: "0600"
    backup: true
    validate: 'sshd -t -f %s'
  notify: Reload sshd

handlers:
  - name: Reload sshd
    ansible.builtin.systemd_service:
      name: sshd
      state: reloaded
```

🔍 **Observation** :

- `%s` est remplacé par le **chemin du fichier temporaire**.
- Si `sshd -t` retourne `0` → `/etc/ssh/sshd_config` est écrasé, handler notifié.
- Si `sshd -t` retourne `!= 0` → fichier intact, tâche **failed**.

**Sans `validate:`** un sshd_config cassé pourrait **bloquer SSH** au prochain
restart — vous perdez l'accès.

## 📚 Exercice 5 — Le piège YAML sur `mode:`

```yaml
- name: Piege mode non quote
  ansible.builtin.copy:
    content: "test\n"
    dest: /tmp/lab-mode-piege.txt
    mode: 0644          # ❌ YAML interprete comme decimal 644 → 0o1204

- name: Bon mode quote
  ansible.builtin.copy:
    content: "test\n"
    dest: /tmp/lab-mode-ok.txt
    mode: "0644"        # ✅ String, parse en octal correctement
```

🔍 **Observation** : sans guillemets, YAML parse `0644` comme **décimal 644**
(rien à voir avec l'octal). Ansible essaie de l'appliquer comme mode → permissions
**aberrantes**.

**Règle** : **toujours** `mode: "0644"` (avec guillemets) ou `mode: "u=rw,g=r,o=r"`
(symbolique).

## 📚 Exercice 6 — `force: false` (ne pas écraser)

```yaml
- name: Deployer config initiale (sans ecraser)
  ansible.builtin.copy:
    src: files/myapp.conf
    dest: /etc/myapp.conf
    force: false
    mode: "0644"
```

🔍 **Observation** :

- Si `/etc/myapp.conf` n'existe pas → fichier créé (`changed`).
- Si existe → tâche **`ok`** (pas de modification, même si le contenu local diffère).

**Cas d'usage** : déploiement d'une config initiale qu'on **laisse l'utilisateur
modifier**. Pratique pour des `motd` ou des templates de config exemple.

## 📚 Exercice 7 — `remote_src: true` (copier depuis le managed node)

`copy: remote_src: true` ne transfère **pas** depuis le control node — il copie
**à l'intérieur du managed node**.

```yaml
- name: Sauvegarder /etc/hosts en /tmp avant modification
  ansible.builtin.copy:
    src: /etc/hosts
    dest: /tmp/hosts.backup
    remote_src: true
    mode: "0644"
```

🔍 **Observation** : `src:` est résolu **côté managed node**, pas côté control
node. Pratique pour des sauvegardes locales avant modification.

## 🔍 Observations à noter

- **`src:`** = fichier local (control node), **`content:`** = inline.
- **Toujours `\n`** à la fin du `content:` — piège classique des parseurs stricts.
- **Toujours `mode: "0644"`** quoté — sinon YAML décimal vs octal.
- **`backup: true`** = filet de sécurité gratuit, à activer sur configs critiques.
- **`validate:`** est obligatoire pour `sshd_config`, `nginx.conf`, `sudoers`.
- **`remote_src: true`** = copie **à l'intérieur** du managed node.
- **`force: false`** = laisser le fichier existant intact (pour configs initiales).

## 🤔 Questions de réflexion

1. Vous voulez déployer un fichier de config qui **inclut le hostname du serveur**.
   Faut-il utiliser `copy: content:` avec `{{ ansible_hostname }}` ou passer à
   `template:` ? Pourquoi ?

2. Avec `backup: true`, où sont créés les backups et comment les nettoyer
   automatiquement après N jours ?

3. Pourquoi `validate: 'sshd -t -f %s'` est **plus sûr** qu'un `validate: 'sshd
   -t'` (sans `%s`) ? Que se passe-t-il sans `%s` ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`directory_mode:`** : mode des **dossiers parents** créés par `copy:` quand
  le `dest:` inclut un chemin profond.
- **`unsafe_writes: true`** : permet l'écriture sur des FS qui ne supportent pas
  `rename atomique` (NFS sans verrous, certaines images Docker).
- **`decrypt: true`** : déchiffre le fichier source si chiffré avec **Ansible
  Vault** — pour pousser des secrets chiffrés en clair sur le managed node.
- **Pattern multi-fichiers** : `copy: src:` accepte un dossier — Ansible **synchronise**
  récursivement (préfixe `src: files/`, slash final = contenu, sans slash = dossier).
- **Lab 32 (file)** : pour gérer **uniquement** les métadonnées (mode, owner,
  state) sans transférer de contenu.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-fichiers/copy/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-fichiers/copy/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-fichiers/copy/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

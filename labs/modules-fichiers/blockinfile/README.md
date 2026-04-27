# Lab 33 — Module `blockinfile:` (bloc multi-lignes idempotent)

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

🔗 [**Module blockinfile Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-blockinfile/)

`ansible.builtin.blockinfile:` insère ou met à jour un **bloc multi-lignes** dans
un fichier existant, avec **idempotence garantie via des markers automatiques**.
C'est le module qui comble le trou entre `lineinfile:` (1 ligne) et `template:`
(fichier complet).

Au prochain run, Ansible cherche les markers (`# BEGIN ...` et `# END ...`),
**remplace tout ce qui est entre les deux** par le nouveau bloc, et regénère les
markers. Conséquence : **idempotence garantie**, jamais de duplication.

Cas d'usage typiques : ajouter **3-10 lignes de durcissement** dans un fichier
système, déposer un **bloc d'aliases** dans `/etc/profile.d/`, gérer une
**section custom** dans un fichier que vous ne contrôlez pas entièrement.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Insérer** un bloc multi-lignes idempotent avec markers automatiques.
2. **Personnaliser** le marker (format, contenu) pour gérer **plusieurs blocs**.
3. **Positionner** le bloc avec `insertafter:` / `insertbefore:`.
4. **Adapter** le format du marker au type de fichier (`#`, `--`, `<!-- -->`).
5. **Choisir** entre `lineinfile:`, `blockinfile:`, et `template:` selon la taille du contenu.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /etc/profile.d/aliases-rhce.sh /etc/ssh/sshd_config.d/99-ansible.conf"
```

## 📚 Exercice 1 — Bloc simple avec marker par défaut

Créez `lab.yml` :

```yaml
---
- name: Demo blockinfile par defaut
  hosts: db1.lab
  become: true
  tasks:
    - name: Bloc d aliases shell
      ansible.builtin.blockinfile:
        path: /etc/profile.d/aliases-rhce.sh
        create: true
        mode: "0644"
        block: |
          alias ll='ls -lah'
          alias gs='git status'
          alias ports='ss -tulpn'
```

**Lancez** :

```bash
ansible-playbook labs/modules-fichiers/blockinfile/lab.yml
ssh ansible@db1.lab 'cat /etc/profile.d/aliases-rhce.sh'
```

🔍 **Observation** : le fichier contient :

```text
# BEGIN ANSIBLE MANAGED BLOCK
alias ll='ls -lah'
alias gs='git status'
alias ports='ss -tulpn'
# END ANSIBLE MANAGED BLOCK
```

**Re-lancer** : `changed=0` (idempotence par marker).

**Modifier le `block:`** (ajouter `alias rm='rm -i'`) puis relancer : `changed=1`,
le bloc est **mis à jour entre les markers**, pas dupliqué.

## 📚 Exercice 2 — Marker custom (plusieurs blocs dans un fichier)

```yaml
- name: Bloc 1 - Durcissement sshd
  ansible.builtin.blockinfile:
    path: /etc/ssh/sshd_config.d/99-ansible.conf
    create: true
    mode: "0600"
    block: |
      PermitRootLogin no
      PasswordAuthentication no
    marker: "# {mark} HARDENING ANSIBLE"

- name: Bloc 2 - Logging custom
  ansible.builtin.blockinfile:
    path: /etc/ssh/sshd_config.d/99-ansible.conf
    block: |
      LogLevel VERBOSE
      SyslogFacility AUTH
    marker: "# {mark} LOGGING ANSIBLE"
```

🔍 **Observation** : le fichier contient **2 blocs distincts**, chacun avec ses
propres markers :

```text
# BEGIN HARDENING ANSIBLE
PermitRootLogin no
PasswordAuthentication no
# END HARDENING ANSIBLE
# BEGIN LOGGING ANSIBLE
LogLevel VERBOSE
SyslogFacility AUTH
# END LOGGING ANSIBLE
```

**Sans marker custom**, les 2 tâches auraient utilisé le même marker par défaut
(`# {mark} ANSIBLE MANAGED BLOCK`) → la 2e tâche aurait **écrasé** la 1ère. Avec
markers custom, **cohabitation** propre.

**`{mark}`** est remplacé par `BEGIN` ou `END`. Convention : nom unique par bloc.

## 📚 Exercice 3 — `insertafter:` / `insertbefore:`

```yaml
- name: Inserer un bloc apres une ligne specifique
  ansible.builtin.blockinfile:
    path: /etc/myapp.conf
    create: true
    mode: "0644"
    block: |
      log_level = INFO
      log_path = /var/log/myapp/
    insertafter: '^\[server\]'
    marker: "# {mark} LOGGING"
```

🔍 **Observation** : si le fichier contient `[server]`, le bloc est inséré
**juste après** cette ligne. Sinon, le bloc est inséré à `EOF` (défaut).

**`insertbefore:`** fait l'inverse — pratique pour ajouter un bloc avant une
section existante (ex : avant `[End]`).

**Piège** : si la regex matche **plusieurs lignes**, c'est la **dernière** qui
gagne (pour `insertafter:`) ou la **première** (pour `insertbefore:`).

## 📚 Exercice 4 — Suppression d'un bloc (`state: absent`)

```yaml
- name: Retirer le bloc HARDENING
  ansible.builtin.blockinfile:
    path: /etc/ssh/sshd_config.d/99-ansible.conf
    marker: "# {mark} HARDENING ANSIBLE"
    state: absent
```

🔍 **Observation** : Ansible cherche les markers `BEGIN HARDENING ANSIBLE` et
`END HARDENING ANSIBLE` et **supprime tout entre les deux** (markers compris).
Le reste du fichier est intact.

**Important** : la suppression nécessite **le marker exact** utilisé à la création.
Si vous changez le `marker:` entre la création et la suppression, le bloc devient
**orphelin** (Ansible ne le trouve plus).

## 📚 Exercice 5 — Adapter le marker au format de fichier

Pour des fichiers où **`#` n'est pas un commentaire**, adapter le marker :

```yaml
# YAML (# est commentaire, OK par defaut)
- ansible.builtin.blockinfile:
    path: /etc/myapp.yml
    block: |
      key1: value1
      key2: value2
    marker: "# {mark} ANSIBLE"

# XML (commentaire = <!-- ... -->)
- ansible.builtin.blockinfile:
    path: /etc/myapp.xml
    block: |
      <option>value1</option>
      <option>value2</option>
    marker: "<!-- {mark} ANSIBLE -->"

# SQL (commentaire = -- ...)
- ansible.builtin.blockinfile:
    path: /etc/myapp.sql
    block: |
      CREATE TABLE foo (...);
      INSERT INTO foo ...;
    marker: "-- {mark} ANSIBLE"

# Python (commentaire = #, OK par defaut)
- ansible.builtin.blockinfile:
    path: /opt/myapp/config.py
    block: |
      DEBUG = True
      LOG_LEVEL = "INFO"
    marker: "# {mark} ANSIBLE"
```

🔍 **Observation** : adapter le marker au format **évite que le fichier devienne
syntaxiquement cassé**. Un `# BEGIN ANSIBLE` dans un fichier XML rendrait le XML
invalide.

## 📚 Exercice 6 — Le piège : 2 tâches `blockinfile:` sans marker custom

```yaml
- name: Bloc 1 (sans marker custom)
  ansible.builtin.blockinfile:
    path: /tmp/lab-blockinfile-piege.txt
    create: true
    block: |
      ligne 1A
      ligne 1B

- name: Bloc 2 (sans marker custom non plus !)
  ansible.builtin.blockinfile:
    path: /tmp/lab-blockinfile-piege.txt
    block: |
      ligne 2A
      ligne 2B
```

**Lancez et inspectez** :

```bash
ansible-playbook labs/modules-fichiers/blockinfile/lab.yml
ssh ansible@db1.lab 'cat /tmp/lab-blockinfile-piege.txt'
```

🔍 **Observation** : le fichier ne contient que **bloc 2** (`ligne 2A`, `ligne 2B`).
Le **bloc 1 a été écrasé** parce que les deux tâches utilisent le **même marker
par défaut** (`# BEGIN ANSIBLE MANAGED BLOCK`).

**Toujours** mettre un **marker unique** par bloc dans le même fichier.

## 📚 Exercice 7 — Comparaison `lineinfile:` vs `blockinfile:` vs `template:`

| Cas | Module recommandé | Pourquoi |
|---|---|---|
| 1 ligne (`PermitRootLogin no`) | `lineinfile:` | Simple, regex |
| 3-10 lignes liées (bloc d'options) | `blockinfile:` | Markers, idempotence |
| Fichier complet possédé | `template:` | Interpolation, validate |
| Plusieurs blocs séparés dans un fichier | `blockinfile:` × N (marker custom) | Cohabitation |
| Fichier qu'on ne possède pas (système) | `blockinfile:` | Modifie sans tout réécrire |

## 🔍 Observations à noter

- **Markers** = `# BEGIN ANSIBLE MANAGED BLOCK` / `# END ...` par défaut.
- **`{mark}` dans `marker:`** est remplacé par `BEGIN` ou `END`.
- **Marker unique par bloc** si plusieurs blocs dans un fichier.
- **`create: true`** crée le fichier s'il n'existe pas.
- **`state: absent`** supprime tout entre les markers.
- **Adapter le format du marker** au type de fichier (`#`, `--`, `<!-- -->`).
- **Toujours `mode: "0644"`** quoté.

## 🤔 Questions de réflexion

1. Vous gérez un fichier `/etc/sysctl.conf` partagé entre plusieurs rôles
   Ansible. Comment **éviter les conflits** entre les blocs gérés par chaque
   rôle ?

2. Quelle est la différence entre `blockinfile:` (avec markers) et `template:` du
   point de vue de la **traçabilité** (qui a modifié quoi) ?

3. Vous voulez ajouter un bloc **avant** une ligne existante dans un fichier.
   Pourquoi `insertbefore:` peut-il poser problème si la regex matche **plusieurs**
   lignes ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`marker_begin:`** / **`marker_end:`** : override fin du marker (au lieu du
  `{mark}` template). Pour des cas où vous voulez des markers vraiment custom.
- **`prepend_newline:`** / **`append_newline:`** : ajouter un saut de ligne avant
  ou après le bloc inséré (utile pour la lisibilité).
- **Pattern `drop-in config`** : préférer **un fichier dédié** dans
  `/etc/<service>.conf.d/99-ansible.conf` géré par `template:` ou `copy:` plutôt
  qu'un `blockinfile:` dans le fichier global. Plus modulaire.
- **Lab 30 (lineinfile vs template)** : comparaison complète des 3 approches.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-fichiers/blockinfile/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-fichiers/blockinfile/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-fichiers/blockinfile/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

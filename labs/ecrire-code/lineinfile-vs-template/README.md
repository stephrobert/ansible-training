# Lab 30 — `lineinfile:` vs `template:` (quand utiliser quoi)

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

🔗 [**lineinfile vs template Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/lineinfile-vs-template/)

Deux modules pour **modifier des fichiers de config**, deux philosophies opposées :

- **`lineinfile:`** = chirurgie ligne par ligne. Vous ne **possédez pas** le fichier
  entier — vous ajoutez/modifiez **1 ou 2 lignes** ciblées par regex. Conserve le
  reste intact.
- **`template:`** = réécriture complète. Vous **possédez** le fichier — vous
  régénérez tout depuis un template Jinja2.

Choisir le mauvais module mène à **deux problèmes différents** :

- `lineinfile:` sur 20 lignes → 20 tâches, regex fragiles, illisible.
- `template:` sur un fichier que vous ne possédez pas → vous écrasez les
  modifications de l'utilisateur ou d'autres outils.

Ce lab démontre les **deux modules** côte à côte sur des cas concrets.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Choisir** entre `lineinfile:` et `template:` selon le scénario.
2. **Utiliser** `lineinfile:` avec `regexp:`, `line:`, `state:`, `backup:`.
3. **Combiner** les deux modules : `template:` pour la base, `lineinfile:` pour des overrides.
4. **Identifier** le seuil où `lineinfile:` devient `blockinfile:` ou `template:`.
5. **Diagnostiquer** un `lineinfile:` qui empile au lieu de remplacer (regex absente).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /etc/myapp.conf*; rm -f /etc/hosts.bak"
```

## 📚 Exercice 1 — `lineinfile:` simple (1 ligne)

```yaml
---
- name: Demo lineinfile - 1 ligne
  hosts: db1.lab
  become: true
  tasks:
    - name: Ajouter une entree DNS dans /etc/hosts
      ansible.builtin.lineinfile:
        path: /etc/hosts
        regexp: '^192\.168\.99\.99\s'
        line: '192.168.99.99 mon-host.lab'
        state: present
        backup: true
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/lineinfile-vs-template/lab.yml
ssh ansible@db1.lab 'cat /etc/hosts'
```

🔍 **Observation** : la ligne `192.168.99.99 mon-host.lab` est ajoutée à
`/etc/hosts`. **Le reste du fichier est intact** — Ansible n'a rien réécrit.

**Re-lancer le playbook** : aucune modification (idempotent grâce au `regexp:`).

## 📚 Exercice 2 — `lineinfile:` avec `regexp:` (modifier une ligne existante)

```yaml
- name: Modifier la valeur de PermitRootLogin
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^#?PermitRootLogin'
    line: 'PermitRootLogin no'
    state: present
    backup: true
    validate: 'sshd -t -f %s'
```

🔍 **Observation** :

- **`regexp:`** matche la ligne **existante** (commentée ou décommentée).
- **`line:`** la **remplace** par la nouvelle valeur.
- **Sans `regexp:`**, Ansible **ajoute** une nouvelle ligne (et empile à chaque run).

**Toujours** mettre `regexp:` quand vous modifiez une option existante. Sans regexp,
au 2e run vous avez **2 lignes `PermitRootLogin no`**.

## 📚 Exercice 3 — `template:` pour un fichier complet

Pour un fichier de config **applicatif** (myapp.conf), `template:` est plus propre.

Créez `templates/myapp.conf.j2` :

```jinja
[server]
host = {{ server.host }}
port = {{ server.port }}
workers = {{ server.workers }}

[database]
url = {{ database.url }}
pool_size = {{ database.pool_size }}
```

```yaml
- name: Generer myapp.conf depuis template
  ansible.builtin.template:
    src: templates/myapp.conf.j2
    dest: /etc/myapp.conf
    owner: root
    group: root
    mode: "0644"
    backup: true
```

🔍 **Observation** : le fichier est **généré complet** depuis le template. Pas
besoin de 5 `lineinfile:` séparés pour 5 sections. Maintenance plus simple.

## 📚 Exercice 4 — Démontrer la différence sur le même fichier

Imaginons qu'on veuille gérer `/etc/myapp.conf` qui a 6 lignes :

**Approche `lineinfile:` (mauvais choix ici)** :

```yaml
- ansible.builtin.lineinfile:
    path: /etc/myapp.conf
    regexp: '^host'
    line: 'host = 0.0.0.0'

- ansible.builtin.lineinfile:
    path: /etc/myapp.conf
    regexp: '^port'
    line: 'port = 8080'

- ansible.builtin.lineinfile:
    path: /etc/myapp.conf
    regexp: '^workers'
    line: 'workers = 4'

# ... 3 autres lineinfile pour [database]
```

🔍 **Problèmes** :

- **6 tâches** au lieu d'1.
- Les **sections `[server]`** et `[database]` ne sont pas gérées (Ansible ne
  comprend pas la structure INI).
- Si une ligne attendue est **absente** au départ, `lineinfile:` l'**ajoute en
  fin de fichier** — pas dans la bonne section !

**Approche `template:` (bon choix)** :

```yaml
- ansible.builtin.template:
    src: templates/myapp.conf.j2
    dest: /etc/myapp.conf
```

→ **1 seule tâche**, structure préservée, code idempotent.

## 📚 Exercice 5 — Combiner les deux : `template:` + `lineinfile:`

Pattern réel : vous générez `nginx.conf` via `template:`, mais vous voulez **ajouter
une ligne** dans `/etc/sysctl.conf` (fichier que vous ne possédez pas, géré par
plusieurs outils).

```yaml
- name: Generer nginx.conf depuis template (controle complet)
  ansible.builtin.template:
    src: templates/nginx.conf.j2
    dest: /etc/nginx/nginx.conf
    validate: 'nginx -t -c %s'
  notify: Reload nginx

- name: Ajouter une ligne dans sysctl.conf (cohabitation avec d autres outils)
  ansible.builtin.lineinfile:
    path: /etc/sysctl.conf
    regexp: '^net.core.somaxconn'
    line: 'net.core.somaxconn = 4096'
  notify: Apply sysctl

handlers:
  - name: Reload nginx
    ansible.builtin.systemd_service:
      name: nginx
      state: reloaded

  - name: Apply sysctl
    ansible.builtin.command: sysctl -p
```

🔍 **Observation** : `template:` pour les fichiers **app-spécifiques** que vous
contrôlez ; `lineinfile:` pour les fichiers **partagés** (`/etc/hosts`,
`/etc/sysctl.conf`, `/etc/security/limits.conf`).

## 📚 Exercice 6 — Le piège : `lineinfile:` sans `regexp:` empile

```yaml
# ❌ Mauvais : pas de regexp
- ansible.builtin.lineinfile:
    path: /tmp/lab-piege.txt
    line: 'option = valeur'
    create: true
```

**Lancez 3 fois** :

```bash
for i in 1 2 3; do
  ansible-playbook labs/ecrire-code/lineinfile-vs-template/lab.yml
done
ssh ansible@db1.lab 'cat /tmp/lab-piege.txt'
```

🔍 **Observation** : sans `regexp:`, Ansible **vérifie si la ligne existe déjà
exactement**. Si vous changez juste un caractère (espace, casse), elle est
ajoutée à nouveau → **fichier qui grossit**.

**Solution** : **toujours** mettre un `regexp:` qui matche la **clé** (`^option\s*=`),
même si la `line:` complète change.

```yaml
# ✅ Bon : regexp sur la cle
- ansible.builtin.lineinfile:
    path: /tmp/lab-piege.txt
    regexp: '^option\s*='
    line: 'option = valeur'
```

## 📚 Exercice 7 — Quand passer de `lineinfile:` à `blockinfile:` ?

`blockinfile:` (lab 33 plus tard) gère **un bloc de plusieurs lignes** avec
markers automatiques. Quand préférer ?

| Cas | Module |
|---|---|
| 1 ligne (`option = valeur`) | `lineinfile:` |
| 2-3 lignes liées (bloc d'options) | `blockinfile:` |
| Fichier complet possédé | `template:` |

**Règle** : si vous avez **3+ `lineinfile:` consécutifs** sur le même fichier,
passer à **`blockinfile:`** (1 tâche, markers, idempotent).

## 🔍 Observations à noter

- **`lineinfile:`** = 1 ligne, **`template:`** = fichier complet.
- **`regexp:`** = obligatoire pour modifier une ligne existante (sinon empile).
- **`backup: true`** + **`validate:`** = combo de sécurité sur les configs critiques.
- **`template:`** sur fichier **possédé** ; **`lineinfile:`** sur fichier **partagé**.
- **3+ `lineinfile:` consécutifs** = passer à `blockinfile:` (lab 33).
- **`lineinfile:` sans `regexp:`** = piège classique (empile à chaque modification de la ligne).

## 🤔 Questions de réflexion

1. Vous voulez modifier `/etc/sudoers` pour ajouter une règle. `lineinfile:` ou
   `template:` ? Pourquoi `validate: 'visudo -cf %s'` est-il **critique** ?

2. Vous générez `/etc/hosts` via `template:` à partir d'un loop sur `groups['all']`.
   Quel est le **risque** comparé à un `lineinfile:` qui ajouterait juste une ligne ?

3. Vous avez 5 lignes à ajouter dans `/etc/sysctl.conf`. Comparez les approches :
   5 `lineinfile:`, 1 `blockinfile:`, ou 1 `template:` complet pour `/etc/sysctl.d/99-myapp.conf`.

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`lineinfile: insertafter:`** / **`insertbefore:`** : positionner la ligne
  ajoutée après/avant un marker. Ex : ajouter après `^# Custom rules` dans sudoers.
- **`replace:`** module : substitution **multi-occurrence** par regex. Différent
  de `lineinfile:` qui ne traite qu'une seule ligne.
- **Pattern `drop-in config`** : éviter de modifier `/etc/<service>.conf` (fichier
  global) ; déposer un fichier custom dans `/etc/<service>.conf.d/99-myapp.conf`
  via `template:`. Plus propre, plus modulaire.
- **`lineinfile: state: absent`** + `regexp:` : **supprimer** une ligne matchant
  le regexp. Pratique pour le **durcissement** (retirer des options dangereuses).

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/lineinfile-vs-template/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/lineinfile-vs-template/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/lineinfile-vs-template/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

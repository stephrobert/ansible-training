# Lab 34 — Module `fetch:` (rapatrier des fichiers)

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

🔗 [**Module fetch Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-fetch/)

`ansible.builtin.fetch:` est l'**inverse exact de `copy:`** — il rapatrie un
fichier depuis un managed node vers le control node. Il sert à collecter des
**logs**, sauvegarder des **configurations existantes** avant migration, ou
récupérer des **rapports** générés par les managed nodes.

`fetch:` gère deux modes d'organisation :

- **`flat: false`** (défaut) : arborescence par hôte → `dest/<host>/<src>`.
- **`flat: true`** : fichier unique dans `dest:` (avec interpolation
  `inventory_hostname` recommandée).

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Comprendre** le mode par défaut (arborescence par hôte) et son intérêt.
2. **Utiliser** `flat: true` avec interpolation `inventory_hostname` pour des
   collectes uniformes.
3. **Échouer** explicitement avec `fail_on_missing: true` quand le fichier doit
   exister.
4. **Distinguer** `fetch:` (fichier persistant) de `slurp:` (lecture en mémoire).
5. **Diagnostiquer** un `dest:` relatif qui se résout au mauvais endroit.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ping
rm -rf collected/
```

## 📚 Exercice 1 — Mode défaut (arborescence par hôte)

Créez `lab.yml` :

```yaml
---
- name: Demo fetch arborescence
  hosts: webservers
  become: true
  tasks:
    - name: Backup sshd_config de chaque webserver
      ansible.builtin.fetch:
        src: /etc/ssh/sshd_config
        dest: collected/backup-default/
```

**Lancez** :

```bash
ansible-playbook labs/modules-fichiers/fetch/lab.yml
tree collected/backup-default/
```

🔍 **Observation** : structure créée :

```text
collected/backup-default/
├── web1.lab/
│   └── etc/
│       └── ssh/
│           └── sshd_config
└── web2.lab/
    └── etc/
        └── ssh/
            └── sshd_config
```

**Avantages** :

- **Pas de risque d'écrasement** entre hôtes (chacun a son sous-dossier).
- **Préserve l'arborescence absolue** — utile pour des audits qui comparent les mêmes chemins.

**Inconvénient** : profondeur d'arborescence importante. Pour un seul fichier
par hôte, c'est beaucoup. → utiliser `flat: true`.

## 📚 Exercice 2 — Mode flat (fichier unique)

```yaml
- name: Recuperer un rapport audit (flat)
  ansible.builtin.fetch:
    src: /etc/os-release
    dest: "{{ inventory_dir }}/../collected/{{ inventory_hostname | regex_replace('\\.lab$', '') }}-os-release.txt"
    flat: true
```

**Lancez** :

```bash
ansible-playbook labs/modules-fichiers/fetch/lab.yml
ls collected/
```

🔍 **Observation** : structure plate :

```text
collected/
├── web1-os-release.txt
└── web2-os-release.txt
```

**Sans `inventory_hostname` dans `dest:`** sur multi-hôtes, **chaque hôte écrase
le précédent** — un seul fichier reste à la fin.

**Règle** : `flat: true` + `dest:` interpolant `{{ inventory_hostname }}`.

## 📚 Exercice 3 — Le piège du `dest:` relatif

```yaml
- name: Fetch avec dest relatif
  ansible.builtin.fetch:
    src: /etc/hostname
    dest: collected/hostname-{{ inventory_hostname }}
    flat: true
```

**Lancez** :

```bash
ansible-playbook labs/modules-fichiers/fetch/lab.yml
find . -name "hostname-*"
```

🔍 **Observation** : le fichier peut atterrir dans `collected/` à la racine du
repo... **OU** dans `labs/modules-fichiers/fetch/collected/`, selon **d'où on
lance ansible-playbook** !

`fetch: dest:` relatif est résolu par rapport au **`playbook_dir`** (dossier du
playbook), **pas** au cwd de l'exécution.

**Solution robuste** : utiliser **`{{ inventory_dir }}/../collected/`** pour
ancrer le chemin sur l'inventaire (toujours stable) :

```yaml
dest: "{{ inventory_dir }}/../collected/hostname-{{ inventory_hostname }}"
```

C'est exactement la correction qu'on a apportée à `inventory/hosts.yml` pour
résoudre les chemins de clés SSH.

## 📚 Exercice 4 — `fail_on_missing: true`

Par défaut, si `src:` n'existe pas, `fetch:` retourne `ok: skipped` (sans erreur).
Sur des collectes critiques, vous voulez **échouer** explicitement.

```yaml
- name: Recuperer un fichier qui n existe peut-etre pas
  ansible.builtin.fetch:
    src: /etc/myapp/license.key
    dest: collected/license-{{ inventory_hostname }}.key
    flat: true
    fail_on_missing: true
```

🔍 **Observation** :

- **Sans `fail_on_missing: true`** : si `/etc/myapp/license.key` n'existe pas, la
  tâche est **skipped silencieusement**. Vous découvrez le manquement plus tard.
- **Avec `fail_on_missing: true`** : la tâche **failed**, le PLAY RECAP affiche
  `failed=N`, vous voyez **immédiatement** le problème.

**Cas d'usage** : audits, backups critiques, collectes de logs forensic.

## 📚 Exercice 5 — `validate_checksum:` (vérification d'intégrité)

`fetch:` valide automatiquement le **checksum** du fichier rapatrié (option
`validate_checksum: true` par défaut). Si le fichier change pendant le transfert,
la tâche échoue.

🔍 **Observation** : pour des fichiers très volumineux (Go), le calcul de
checksum peut être lent. **Désactiver** est possible (`validate_checksum: false`)
mais à utiliser uniquement si vous acceptez le risque de corruption silencieuse.

## 📚 Exercice 6 — Pattern audit multi-hôtes

```yaml
---
- name: Audit configurations critiques
  hosts: all
  become: true
  tasks:
    - name: Recuperer sshd_config de chaque host
      ansible.builtin.fetch:
        src: /etc/ssh/sshd_config
        dest: "{{ inventory_dir }}/../collected/audit-{{ ansible_date_time.date }}/sshd_config-{{ inventory_hostname }}"
        flat: true
        fail_on_missing: true

    - name: Recuperer ip a list
      ansible.builtin.shell: "ip -j a show > /tmp/ip-state-{{ inventory_hostname }}.json"
      changed_when: false

    - name: Rapatrier l etat reseau
      ansible.builtin.fetch:
        src: "/tmp/ip-state-{{ inventory_hostname }}.json"
        dest: "{{ inventory_dir }}/../collected/audit-{{ ansible_date_time.date }}/network-{{ inventory_hostname }}.json"
        flat: true
```

🔍 **Observation** : pattern complet **audit + collecte centralisée** avec
horodatage du jour.

## 📚 Exercice 7 — `fetch:` vs `slurp:`

`slurp:` (autre module Ansible) **lit** un fichier distant et le retourne en
**base64** dans une variable, sans écrire sur le control node.

```yaml
- name: Lire le contenu d un fichier sans le sauver
  ansible.builtin.slurp:
    src: /etc/hostname
  register: hostname_content

- name: Decoder et utiliser
  ansible.builtin.debug:
    msg: "Hostname raw : {{ hostname_content.content | b64decode }}"
```

| Cas | Module |
|---|---|
| Sauvegarder le fichier en local | `fetch:` |
| Lire le contenu en mémoire pour traitement | `slurp:` |
| Comparer le contenu avant action | `slurp:` puis filter |
| Backup massif | `fetch:` |

🔍 **Observation** : `slurp:` est plus léger (pas d'écriture disque) mais ne
laisse aucune trace. Préférer `fetch:` quand vous voulez un audit trail.

## 🔍 Observations à noter

- **`fetch:`** = inverse de `copy:` — du managed node vers le control node.
- **Mode défaut** : arborescence par hôte (sûr, jamais d'écrasement).
- **`flat: true`** : fichier unique, **toujours interpoler `inventory_hostname`** sur multi-hôtes.
- **`fail_on_missing: true`** sur les collectes critiques (sinon les manques sont silencieux).
- **`dest:` relatif** est résolu depuis `playbook_dir` — préférer `{{ inventory_dir }}/../`.
- **`slurp:`** lit en mémoire (base64), **`fetch:`** sauve sur disque.

## 🤔 Questions de réflexion

1. Vous voulez collecter `/var/log/messages` des 50 serveurs **en parallèle** dans
   un dossier centralisé daté. Combinez `fetch:`, `flat:`, `inventory_hostname`,
   et `ansible_date_time` — quel `dest:` ?

2. `fetch:` valide le **checksum** par défaut. Pourquoi le **désactiver** sur de
   gros fichiers est-il un compromis dangereux ?

3. Quand utiliser `slurp:` vs `fetch:` pour vérifier qu'un fichier de config
   contient une string précise sur tous les managed nodes ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **Pattern `archive: + fetch:`** : créer un tarball côté managed node, puis le
  rapatrier en une seule opération. Utile pour collecter **plusieurs fichiers**
  sans 10 `fetch:`.
- **Compression à la volée** : `fetch:` ne compresse pas — passer par `archive:`
  d'abord (lab 35).
- **`add_host:` + `fetch:`** : pattern dynamique pour collecter depuis un host
  généré au runtime.
- **rsync via `synchronize:`** (collection ansible.posix) : pour des collectes
  bidirectionnelles avec delta minimal. Plus puissant mais plus lourd.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-fichiers/fetch/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-fichiers/fetch/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-fichiers/fetch/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

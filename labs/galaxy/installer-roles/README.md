# Lab 74 — `requirements.yml` : installer rôles & collections depuis Galaxy / Git

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis : Ansible installé. Pas besoin des VMs (lab purement local).

## 🧠 Rappel

🔗 [**Installer des rôles via requirements.yml**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/installer-roles-galaxy/)

Un fichier `requirements.yml` est l'**équivalent Ansible** de `package.json`
(Node), `requirements.txt` (Python) ou `Gemfile` (Ruby). Il déclare **toutes
les dépendances** d'un projet — rôles **et** collections — avec sources
(Galaxy ou Git) et versions épinglées.

```yaml
# requirements.yml
roles:
  - name: geerlingguy.docker      # Galaxy
    version: 7.4.4

  - src: https://github.com/foo/bar    # Git
    name: foo.bar
    version: v1.2.0

collections:
  - name: ansible.posix
    version: ">=1.5.0,<2.0.0"          # plage SemVer
```

→ Installation : `ansible-galaxy install -r requirements.yml` (rôles)
+ `ansible-galaxy collection install -r requirements.yml` (collections).

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Écrire un **`requirements.yml`** mixant rôles Galaxy + Git + collections.
2. **Pinner les versions** (exact, plage SemVer, tag Git, branche).
3. Différencier **Galaxy** (auteur.role) et **Git** (URL clonable).
4. Comprendre `~/.ansible/roles/` vs `~/.ansible/collections/`.
5. **Vendoriser** un rôle dans le repo (`-p roles/`).
6. Préparer un projet Ansible **reproductible** (`requirements.yml` versionné).

## 🔧 Préparation

```bash
ansible-galaxy --version
```

## ⚙️ Arborescence

```text
labs/galaxy/installer-roles/
├── README.md
├── Makefile
├── requirements.yml         ← le manifeste à étudier
└── roles/                    ← cible d'installation locale (vendoring)
```

## 📚 Exercice 1 — Lire le `requirements.yml` livré

```yaml
---
roles:
  # 1. Rôle Galaxy public (avec version pinnée)
  - name: geerlingguy.docker
    version: 7.4.4

  # 2. Rôle depuis Git (branche main)
  - src: https://github.com/stephrobert/ansible-role-motd
    name: stephrobert.motd
    version: main

  # 3. Rôle depuis Git avec tag
  - src: https://github.com/geerlingguy/ansible-role-postgresql
    name: geerlingguy.postgresql
    version: 4.1.0

collections:
  - name: ansible.posix
    version: ">=1.5.0,<2.0.0"

  - name: community.general
    version: ">=8.0.0"

  - name: community.crypto
    version: "2.20.0"          # ← exact match production

  - name: ansible.utils
    version: ">=4.0.0"
```

🔍 **Observation** : 3 rôles (1 Galaxy + 2 Git) et 4 collections.
Chacun **pinne** sa version pour reproductibilité.

## 📚 Exercice 2 — Installer dans `~/.ansible/`

```bash
cd labs/galaxy/installer-roles/
ansible-galaxy role install -r requirements.yml
ansible-galaxy collection install -r requirements.yml

ansible-galaxy role list
ansible-galaxy collection list
```

🔍 **Observation** : par défaut, les rôles vont dans `~/.ansible/roles/` et
les collections dans `~/.ansible/collections/ansible_collections/`.

## 📚 Exercice 3 — Vendoriser dans `roles/` du projet

```bash
ansible-galaxy role install -r requirements.yml -p roles/
ansible-galaxy collection install -r requirements.yml -p collections/
```

🔍 **Observation** : `-p` (path) installe **dans le repo lui-même**. C'est
le pattern **vendoring** : on commit les rôles tiers pour avoir un projet
reproductible **sans réseau**.

> ⚠️ **Pas de standard absolu** : certains commitent (sécurité,
> reproductibilité), d'autres non (taille du repo). Le `requirements.yml`
> versionné suffit dans la plupart des cas.

## 📚 Exercice 4 — Pinning fin (versions, tags, branches)

| Forme | Exemple | Effet |
| --- | --- | --- |
| Version Galaxy exacte | `version: 7.4.4` | Reproductible strict |
| Plage SemVer | `version: ">=1.5.0,<2.0.0"` | Patch automatique sans breaking |
| Tag Git | `version: v2.0.1` | Reproductible (même commit pour ce tag) |
| Branche Git | `version: main` | **Non reproductible** (main bouge) |
| Commit SHA | `version: abc1234...` | Reproductible **maximum** |

🔍 **Recommandation production** : version exacte ou commit SHA. Branche
`main` interdite (risque silent breaking change à la prochaine install).

## 📚 Exercice 5 — Stratégie d'organisation

Pour un repo Ansible production, organiser :

```text
projet/
├── requirements.yml          ← versionné
├── ansible.cfg               ← roles_path = roles:~/.ansible/roles
├── roles/                    ← rôles internes au projet
├── collections/              ← collections vendoring (optionnel)
├── playbooks/
└── .github/workflows/ci.yml  ← installer requirements en CI
```

```ini
# ansible.cfg
[defaults]
roles_path = roles:~/.ansible/roles
collections_path = collections:~/.ansible/collections
```

🔍 **Observation** : `roles_path` priorise les **rôles internes** du projet,
puis fallback sur les rôles tiers installés via `requirements.yml`.

## 🔍 Observations à noter

- **`requirements.yml`** à la racine du projet, **versionné dans Git**.
- **Pinning strict** sur la **production**. Plages `>=` réservées aux
  bibliothèques internes ou à la dev.
- **Branche `main`** = NoGo en production (silently breaking).
- **Vendoring** (`-p roles/` + commit) si reproductibilité offline critique.
- **CI** : `ansible-galaxy install -r requirements.yml` en première étape.

## 🤔 Questions de réflexion

1. Vous avez `version: ">=8.0.0"`. Une nouvelle version `9.0.0` sort —
   est-elle installée si vous re-roulez `ansible-galaxy install` ? Pourquoi ?

2. Différence entre `ansible-galaxy install -r requirements.yml` et
   `ansible-galaxy install -r requirements.yml --force` ?

3. Vous voulez utiliser la **HEAD** d'un repo Git mais aussi être
   reproductible. Comment faire ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md).

## 💡 Pour aller plus loin

- **`signatures:`** sur les collections : vérification GPG (RHCE 2026).
- **`ANSIBLE_GALAXY_TOKEN`** : auth pour Galaxy privé.
- **`server_list:`** dans `ansible.cfg` : multi-Galaxy (privé + public).
- **AAP automation hub** : Galaxy Red Hat privé pour entreprise.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/galaxy/installer-roles/
```

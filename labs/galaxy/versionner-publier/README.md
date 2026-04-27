# Lab 76 — Versionner & publier un rôle (semver, tags Git, Galaxy)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis : Ansible installé, `git` configuré. Pas besoin des VMs.

## 🧠 Rappel

🔗 [**Versionner et publier un rôle Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/versionner-publier/)

Un rôle Ansible **publié** doit être :

- **Versionné** en SemVer (`MAJOR.MINOR.PATCH`).
- Accompagné d'un **`CHANGELOG.md`** au format
  [Keep a Changelog](https://keepachangelog.com/) (sections Added /
  Changed / Fixed / Deprecated / Removed / Security).
- **Tagué** sur Git (`git tag v1.2.0`).
- **Pinable** depuis un `requirements.yml` consommateur.

C'est l'aboutissement du cycle de vie : **écrire → tester → publier →
consommer pinné**.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Appliquer **SemVer** : quand bumper MAJOR / MINOR / PATCH.
2. Écrire un **`CHANGELOG.md`** au format Keep a Changelog.
3. **Tagger** un release Git avec message annoté.
4. **Publier** sur Galaxy via webhook GitHub ou via CLI.
5. Documenter le **pinning** côté consommateur.
6. Automatiser la release via **CI/CD** (workflow tag → publish).

## 🔧 Préparation

```bash
git --version
ansible-galaxy --version
```

## ⚙️ Arborescence

```text
labs/galaxy/versionner-publier/
├── README.md
├── Makefile
├── CHANGELOG.md           ← Keep a Changelog avec ≥ 2 versions
├── PUBLISH.md             ← procédure de publication
└── roles/webserver/        ← rôle exemple à publier
```

## 📚 Exercice 1 — Lire `CHANGELOG.md`

```markdown
# Changelog — rôle webserver

## [1.2.0] - 2026-04-26

### Added
- Support multi-distribution (RHEL, AlmaLinux, Debian via vars/<os_family>.yml)
- Variable `webserver_worker_processes` configurable
- Validation argument_specs.yml

### Changed
- Module `package` (agnostique) au lieu de `dnf` direct

### Fixed
- Idempotence handlers (Reload nginx déclenché 2× résolu)
```

🔍 **Observation** : 3 sections distinctes (`Added`, `Changed`, `Fixed`)
classifient les changements. **Sans `CHANGELOG.md`**, l'utilisateur d'un
upgrade ne sait pas si c'est un breaking change.

## 📚 Exercice 2 — Règles SemVer

| Bump | Quand | Exemple |
| --- | --- | --- |
| **MAJOR** (1.x.x → 2.0.0) | Breaking change : variable supprimée/renommée, structure cassée | Renommer `nginx_listen` → `webserver_listen` |
| **MINOR** (1.0.x → 1.1.0) | Nouvelle feature **rétrocompatible** | Ajouter `webserver_workers` (défaut = ancien comportement) |
| **PATCH** (1.0.0 → 1.0.1) | Bugfix sans changement d'API | Fixer un handler qui se déclenche 2 fois |

🔍 **Règle d'or** : **`1.0.0 → 2.0.0`** signale aux consommateurs qu'ils
doivent **lire le CHANGELOG** et migrer leur code.

## 📚 Exercice 3 — Tagger un release

```bash
# 1. S'assurer que les tests passent
molecule test
ansible-lint --profile production roles/webserver/

# 2. Mettre à jour CHANGELOG.md (ajouter section [1.2.0])
$EDITOR CHANGELOG.md

# 3. Commit + tag annoté
git add CHANGELOG.md
git commit -m "release: v1.2.0"
git tag -a v1.2.0 -m "Release v1.2.0 — Multi-distro support"

# 4. Push tag
git push origin main --tags
```

🔍 **Observation** : `git tag -a` (annoté) **>>** `git tag` (lightweight) :
le tag annoté contient un message + auteur + date, ce qui est ce que
Galaxy lit pour la release notes.

## 📚 Exercice 4 — Publication Galaxy

### Méthode 1 — Webhook GitHub (rôles, recommandé)

1. Sur https://galaxy.ansible.com → **My Content → Add Content → Import
   Role from GitHub**.
2. Sélectionner `<user>/ansible-role-webserver`.
3. À chaque **nouveau tag SemVer**, Galaxy déclenche un import automatique.

### Méthode 2 — CLI (collections, mandatory)

```bash
cd path/to/collection/
ansible-galaxy collection build           # → user-collection-1.2.0.tar.gz
ansible-galaxy collection publish \
  user-collection-1.2.0.tar.gz \
  --api-key=$GALAXY_TOKEN
```

🔍 **Observation** : `--api-key` (et non `--token`) accepte un token
généré sur https://galaxy.ansible.com/me/preferences.

## 📚 Exercice 5 — Lire `PUBLISH.md`

Le fichier livré explique :

- Le **workflow Git** (test → CHANGELOG → commit → tag → push).
- Les **2 méthodes** de publication (webhook vs CLI).
- Le **pinning consommateur** dans `requirements.yml`.
- Le **CI/CD** automatisé (workflow GitHub Actions sur tag).

## 📚 Exercice 6 — Pinning chez le consommateur

```yaml
# requirements.yml d'un autre projet qui consomme votre rôle
roles:
  - src: stephrobert.webserver
    version: 1.2.0          # exact match production

  # Ou plage SemVer
  - src: stephrobert.webserver
    version: ">=1.2.0,<2.0.0"
```

🔍 **Observation** : la plage `>=1.2.0,<2.0.0` autorise les patch + minor
(rétrocompat) mais bloque le saut MAJOR. C'est le pattern **prod
pragmatique**.

## 🔍 Observations à noter

- **SemVer + CHANGELOG** = contrat de **stabilité** avec vos
  utilisateurs.
- **Tag annoté** (`git tag -a`) > tag lightweight pour Galaxy.
- **Webhook Galaxy** est l'option **paresseuse efficace** pour les rôles.
- **Collections** (publication) = obligatoirement via CLI + token.
- **Releases automatisées** via CI/CD : tag → workflow → Galaxy publish.

## 🤔 Questions de réflexion

1. Vous renommez `nginx_user` → `webserver_user`. Quel bump SemVer ?
   Comment migrer les utilisateurs sans casser ?

2. Vous voulez **rétrograder** un release (rollback). Comment faire sur
   Galaxy ? (Indice : il n'y a pas vraiment de delete propre.)

3. Différence entre publier un **rôle** (1 fichier `meta/main.yml`) et une
   **collection** (`galaxy.yml` + `.tar.gz`) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md).

## 💡 Pour aller plus loin

- **`towncrier`** : générateur automatique de CHANGELOG (Python, mais
  applicable Ansible).
- **`semantic-release`** : automatisation tag + CHANGELOG + publish.
- **GitHub Releases** : génération auto des release notes depuis le
  CHANGELOG.
- **Pre-release SemVer** : `1.2.0-rc1`, `1.2.0-beta.1` (acceptés Galaxy).

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/galaxy/versionner-publier/
```

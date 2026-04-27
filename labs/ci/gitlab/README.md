# Lab 70 — CI/CD : GitLab CI

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis local : aucun. Pour exécuter : un projet GitLab (instance
> SaaS gitlab.com ou self-hosted).

## 🧠 Rappel

🔗 [**CI Ansible avec GitLab CI**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/ci-gitlab/)

GitLab CI est l'**équivalent GitLab** de GitHub Actions :

| GitHub Actions | GitLab CI |
| --- | --- |
| `.github/workflows/test.yml` | `.gitlab-ci.yml` (à la racine) |
| `jobs:` | `stages:` + jobs |
| `strategy.matrix:` | `parallel:matrix:` |
| `actions/checkout@v4` | (auto, déjà cloné) |
| `runs-on: ubuntu-latest` | `image:` (n'importe quelle image Docker) |

GitLab CI a un **avantage clé** sur GitHub Actions : **Docker-in-Docker
natif** — utile pour Molecule + Podman/Docker. Plus simple à configurer.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Écrire `.gitlab-ci.yml` avec **stages** : lint, test, release.
2. Utiliser **`parallel:matrix:`** pour multi-distros / multi-versions.
3. Déclarer des **`rules:`** : tests sur PR, release uniquement sur tag.
4. Cache pip via **`cache:`** stage-level.
5. Stocker un job **release** sur Galaxy (uniquement sur tag git).

## 🔧 Préparation

Aucune installation locale.

## ⚙️ Arborescence

```text
labs/ci/gitlab/
├── README.md
├── Makefile
├── .gitlab-ci.yml        ← pipeline complet
└── roles/webserver/
```

## 📚 Exercice 1 — Squelette `.gitlab-ci.yml`

```yaml
---
stages:
  - lint
  - test
  - release

default:
  image: python:3.12-slim
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - .cache/pip

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  PYTHONUNBUFFERED: "1"

ansible-lint:
  stage: lint
  before_script:
    - pip install ansible-lint yamllint
  script:
    - yamllint .
    - ansible-lint --profile production
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"

molecule-test:
  stage: test
  needs: [ansible-lint]
  image: quay.io/ansible/community-ansible-dev-tools:latest
  parallel:
    matrix:
      - DISTRO:
          - quay.io/centos/centos:stream10
          - docker.io/library/debian:12
          - docker.io/library/ubuntu:24.04
        ANSIBLE_VERSION: ["2.16", "2.17", "2.18"]
  script:
    - pip install ansible-core==${ANSIBLE_VERSION}.*
    - molecule test
  variables:
    MOLECULE_DISTRO: $DISTRO

galaxy-release:
  stage: release
  rules:
    - if: $CI_COMMIT_TAG
  image: python:3.12-slim
  before_script:
    - pip install ansible-core
  script:
    - ansible-galaxy role import --token $GALAXY_TOKEN
        --branch $CI_COMMIT_REF_NAME
        $CI_PROJECT_NAMESPACE $CI_PROJECT_NAME
```

🔍 **Observation** :

- **3 stages** : lint → test → release.
- **`needs:`** : `molecule-test` ne tourne que si `ansible-lint` passe.
- **`parallel:matrix:`** : 9 jobs (3 distros × 3 versions).
- **`rules:`** : `galaxy-release` ne tourne **que sur un tag** Git.

## 📚 Exercice 2 — `rules:` (quand exécuter)

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"     # MR ouverte
  - if: $CI_COMMIT_BRANCH == "main"                       # push sur main
  - if: $CI_COMMIT_TAG                                    # tag git (release)
```

🔍 **Observation** : `rules:` remplacent l'ancien `only:` / `except:`. Plus
expressif.

## 📚 Exercice 3 — Cache pip

```yaml
default:
  cache:
    key: ${CI_COMMIT_REF_SLUG}     # cache par branche
    paths:
      - .cache/pip
```

🔍 **Observation** : cache **par branche**. Une PR a son cache propre,
ne pollue pas main.

## 📚 Exercice 4 — Variables protégées (Galaxy token)

Dans GitLab UI : Settings → CI/CD → Variables :

```text
GALAXY_TOKEN = <token Ansible Galaxy>
Protected: ✓     (uniquement sur branches/tags protégés)
Masked: ✓        (caché dans les logs)
```

🔍 **Observation** : **jamais** mettre un token en clair dans
`.gitlab-ci.yml`. Toujours via variables CI/CD.

## 📚 Exercice 5 — `ansible-galaxy role import`

```yaml
script:
  - ansible-galaxy role import --token $GALAXY_TOKEN
      --branch $CI_COMMIT_REF_NAME
      $CI_PROJECT_NAMESPACE $CI_PROJECT_NAME
```

🔍 **Observation** : l'import Galaxy à partir de GitHub/GitLab est **automatique** —
pas besoin d'uploader un .tar.gz. Galaxy clone le repo au tag spécifié.

## 🔍 Observations à noter

- **GitLab CI = GitHub Actions** sur le fond, syntaxe différente.
- **`parallel:matrix:`** simplifie les multi-jobs.
- **`rules:`** = expressivité maximale (regex sur branch, tag, MR…).
- **Variables CI/CD masquées + protégées** = standard sécurité.
- **GitLab self-hosted** : si vous avez votre propre instance, runners
  gratuits illimités.

## 🤔 Questions de réflexion

1. Comment adapter votre solution si la cible passait de **1 host** à un
   parc de **50 serveurs** ? Quels paramètres (`forks`, `serial`, `strategy`)
   faudrait-il ajuster pour conserver des temps d'exécution acceptables ?

2. Quels modules Ansible alternatifs auriez-vous pu utiliser pour atteindre
   le même résultat ? Quels sont leurs trade-offs (idempotence garantie,
   performance, dépendances de collection externe) ?

3. Si une étape du playbook échoue en cours d'exécution, quel est l'impact
   sur les hôtes déjà traités ? Comment rendre le scénario reprenable
   (`block/rescue/always`, `--start-at-task`, `serial`) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md).

## 💡 Pour aller plus loin

- **`include:`** : factorer le pipeline dans un `.gitlab-ci-template.yml`
  partagé entre plusieurs rôles.
- **GitLab Pages** : auto-publier la doc générée par `ansible-doc -t role`
  sur GitLab Pages.
- **GitLab CI Runner Kubernetes** : runners qui scalent automatiquement
  sur K8s.
- **Comparaison** : si votre rôle vit sur GitHub mais que vous voulez
  utiliser GitLab CI, configurez un mirror.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/ci/gitlab/
```

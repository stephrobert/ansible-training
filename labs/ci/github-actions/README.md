# Lab 69 — CI/CD : GitHub Actions

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis local : aucun (vous écrivez juste un workflow YAML). Pour
> exécuter : un compte GitHub + un fork de votre rôle.

## 🧠 Rappel

🔗 [**CI Ansible avec GitHub Actions**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/ci-github-actions/)

Une CI **complète** pour un rôle Ansible orchestre, à chaque PR :

```text
1. Lint (ansible-lint --profile production + yamllint)
2. Test Molecule (matrice OS × versions Ansible)
3. (optionnel) Publication sur Galaxy si tag git
```

GitHub Actions est gratuit pour repos publics, idéal pour les rôles open
source.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Écrire `.github/workflows/test.yml` avec **2 jobs** (lint + molecule).
2. Utiliser **`strategy.matrix`** pour tester N distros × M versions
   Ansible **en parallèle**.
3. Cacher le `pip install` entre runs avec **`actions/setup-python@v5`**.
4. Configurer des **permissions minimales** (`permissions: read-all`).
5. Désactiver `persist-credentials: false` sur `actions/checkout` (sécurité).

## 🔧 Préparation

Aucune installation locale. Optionnel : `act` pour exécuter des workflows
GitHub Actions localement (debug).

## ⚙️ Arborescence

```text
labs/ci/github-actions/
├── README.md
├── Makefile
├── requirements.yml                    ← collections + roles
├── roles/webserver/
└── .github/
    └── workflows/
        └── test.yml                    ← workflow CI complet
```

## 📚 Exercice 1 — Squelette du workflow

```yaml
---
name: Test webserver role

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: "0 6 * * 1"     # lundi matin (anti-rot)

permissions: read-all       # principe du moindre privilège

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false      # sécurité

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - run: pip install ansible-lint yamllint
      - run: yamllint .
      - run: ansible-lint --profile production

  molecule:
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      fail-fast: false
      matrix:
        distro:
          - quay.io/centos/centos:stream10
          - docker.io/library/debian:12
          - docker.io/library/ubuntu:24.04
        ansible_version: ["2.16", "2.17", "2.18"]

    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - run: |
          pip install molecule molecule-plugins[podman]
          pip install ansible-core>=${{ matrix.ansible_version }},<$(echo ${{ matrix.ansible_version }} | awk -F. '{print $1"."$2+1}')

      - run: molecule test
        env:
          MOLECULE_DISTRO: ${{ matrix.distro }}
```

🔍 **Observation** :

- **`needs: lint`** : le job `molecule` ne tourne que si `lint` passe.
- **`fail-fast: false`** : si une combinaison échoue, on continue les
  autres pour avoir un rapport complet.
- **`matrix.distro × matrix.ansible_version`** = **9 jobs en parallèle**.

## 📚 Exercice 2 — Permissions minimales

```yaml
permissions: read-all
# OU plus précis :
permissions:
  contents: read
  pull-requests: write       # uniquement si on commente la PR
```

🔍 **Observation** : par défaut, `GITHUB_TOKEN` a beaucoup de droits. En
production, on **réduit au strict nécessaire** pour limiter le blast
radius en cas de workflow compromis.

## 📚 Exercice 3 — `persist-credentials: false`

```yaml
- uses: actions/checkout@v4
  with:
    persist-credentials: false
```

🔍 **Observation** : par défaut, `actions/checkout` laisse le
`GITHUB_TOKEN` accessible sur le filesystem du runner. Si une dépendance
malveillante l'exfiltre, c'est game over. Désactivez-le sauf si vous
en avez explicitement besoin (pour pousser un commit auto par exemple).

## 📚 Exercice 4 — Cache pip

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
    cache: pip
```

🔍 **Observation** : sans cache, chaque run réinstalle ~50 paquets pip
(~30 s). Avec cache, c'est ~5 s. Sur 9 jobs matrix, ça change la durée
totale de la CI.

## 📚 Exercice 5 — Schedule (anti-rot)

```yaml
on:
  schedule:
    - cron: "0 6 * * 1"     # lundi matin
```

🔍 **Observation** : un rôle peut **se casser** sans qu'on touche au
code (Ansible upstream change, distrib upgrade). Lancer la CI
hebdomadairement détecte les régressions silencieuses.

## 🔍 Observations à noter

- **`needs:`** chaîne les jobs (lint → molecule).
- **`strategy.matrix`** = parallélisation gratuite. Multi-distro × multi-version
  en quelques lignes YAML.
- **Permissions minimales** + **`persist-credentials: false`** =
  défense en profondeur.
- **`schedule`** = détecter les régressions silencieuses (anti-rot).
- **GitHub Actions est gratuit** sur repos publics. Sur repos privés :
  2000 minutes/mois gratuites, puis facturé.

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

- **`act`** (local) : `act -W .github/workflows/test.yml` exécute le
  workflow sur votre poste.
- **Reusable workflows** : `uses: org/.github/workflows/ansible-test.yml@main`
  pour mutualiser entre plusieurs rôles.
- **Dependabot** : auto-PR pour mettre à jour les versions des actions
  (`actions/checkout@v4` → `v5`).
- **GitGuardian / TruffleHog** : ajouter un job de scan de secrets en
  plus de pre-commit.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/ci/github-actions/
```

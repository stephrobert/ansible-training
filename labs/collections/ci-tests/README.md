# Lab 96 — Pipeline CI matrice `ansible-core` × Python pour une collection

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `make bootstrap && make provision` à la racine du repo.

## 🧠 Rappel

🔗 [**Pipeline CI pour collections**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/pipeline-ci/)

Une collection en production se **teste sur plusieurs versions** d'`ansible-core` et de Python pour garantir la **compatibilité descendante**. Le pattern 2026 : **GitHub Actions** avec une **matrice** `ansible-core × python`, exécutant **`ansible-test sanity`** + **`ansible-test units`** + **`ansible-lint --strict`** dans un Docker conforme, avec **SHA pinning** des actions et **`permissions: {}`** au global.

Ce lab fournit le workflow GitHub Actions complet (et son équivalent GitLab CI), durci selon les pratiques 2026.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Écrire un **workflow GitHub Actions** pour une collection.
2. Configurer une **matrice** `ansible-core stable-2.18 × stable-2.19 × devel × Python 3.11 × 3.12`.
3. Lancer **`ansible-test sanity --docker`** dans la CI.
4. Lancer **`ansible-test units --docker`** sur les modules Python.
5. **Pinner** les actions par **SHA** (zizmor compliant).
6. Ajouter **`permissions: {}`** + **`persist-credentials: false`**.
7. Écrire l'**équivalent GitLab CI** avec stages `lint`, `sanity`, `units`.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ansible.builtin.ping
zizmor --version 2>/dev/null || pipx install zizmor
```

## ⚙️ Arborescence cible

```text
labs/collections/ci-tests/
├── README.md                            ← ce fichier (tuto guidé)
├── Makefile                             ← cible clean
└── challenge/
    ├── README.md                        ← consigne challenge
    └── tests/
        └── test_ci.py                   ← tests structurels (workflow + .gitlab-ci.yml)
```

L'apprenant écrit lui-même les fichiers `.github/workflows/ansible-test.yml` et `.gitlab-ci.yml` dans `challenge/`.

## 📚 Exercice 1 — Anatomie d'un workflow GitHub Actions matrice

```yaml
# .github/workflows/ansible-test.yml
name: Ansible test
on:
  push:
    branches: [main]
  pull_request:

permissions: {}                          # ← global = aucune

jobs:
  sanity:
    name: sanity (${{ matrix.ansible }} / py${{ matrix.python }})
    runs-on: ubuntu-24.04
    permissions:
      contents: read
    strategy:
      fail-fast: false                   # ← continue même si une combo échoue
      matrix:
        ansible:
          - stable-2.18
          - stable-2.19
          - devel
        python:
          - "3.11"
          - "3.12"
    steps:
      - name: Checkout
        uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.2.2
        with:
          path: ansible_collections/student/lab96
          persist-credentials: false

      - name: Setup Python
        uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065  # v5.6.0
        with:
          python-version: "${{ matrix.python }}"

      - name: Install ansible-core ${{ matrix.ansible }}
        run: |
          pip install "https://github.com/ansible/ansible/archive/${{ matrix.ansible }}.tar.gz"

      - name: ansible-test sanity --docker
        working-directory: ansible_collections/student/lab96
        run: |
          ansible-test sanity --docker default -v --color
```

🔍 **Observation** : la **matrice** lance `3 × 2 = 6` jobs en parallèle. **`fail-fast: false`** continue même si une combo casse (utile pour voir lesquelles passent). **`permissions: {}`** au global, élargi par job au strict nécessaire.

## 📚 Exercice 2 — Pinning par SHA des actions

Toutes les actions externes **doivent** être pinnées par **SHA 40 caractères** :

| Action | SHA (exemple 2026) | Tag équivalent |
|--------|-------------------|----------------|
| `actions/checkout` | `b4ffde65f46336ab88eb53be808477a3936bae11` | v4.2.2 |
| `actions/setup-python` | `a26af69be951a213d495a4c3e4e4022e16d87065` | v5.6.0 |

🔍 **Observation cruciale** : sans SHA pinning, un attaquant qui compromet le repo `actions/checkout` peut **repush** le tag `v4.2.2` sur un commit malicieux. Tous les pipelines `uses: actions/checkout@v4.2.2` exécutent alors le code malicieux. **Zizmor** vérifie ce pattern.

## 📚 Exercice 3 — `persist-credentials: false`

```yaml
- uses: actions/checkout@<SHA>
  with:
    persist-credentials: false           # ← bloque le token Git après le checkout
```

🔍 **Observation** : sans cette option, le `GITHUB_TOKEN` reste dans `.git/config` et peut être **exfiltré** par une étape suivante compromise. Pattern **systématique** sur `actions/checkout` en 2026.

## 📚 Exercice 4 — Job `units` (tests Python)

```yaml
  units:
    name: units (${{ matrix.ansible }} / py${{ matrix.python }})
    runs-on: ubuntu-24.04
    permissions: { contents: read }
    strategy:
      fail-fast: false
      matrix:
        ansible: [stable-2.18, devel]
        python: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.2.2
        with:
          path: ansible_collections/student/lab96
          persist-credentials: false

      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065  # v5.6.0
        with:
          python-version: "${{ matrix.python }}"

      - run: |
          pip install "https://github.com/ansible/ansible/archive/${{ matrix.ansible }}.tar.gz"

      - name: ansible-test units --docker
        working-directory: ansible_collections/student/lab96
        run: |
          ansible-test units --docker default -v --color --python ${{ matrix.python }}
```

🔍 **Observation** : `ansible-test units` lance **pytest** sur les fichiers `tests/unit/plugins/...` de la collection. **Coverage activée** par défaut depuis 2.16. Bloquer la CI si la couverture chute sous un seuil avec `--coverage --coverage-check`.

## 📚 Exercice 5 — Ajouter `ansible-lint --strict`

```yaml
  lint:
    name: ansible-lint
    runs-on: ubuntu-24.04
    permissions: { contents: read }
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11
        with:
          path: ansible_collections/student/lab96
          persist-credentials: false

      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
        with: { python-version: "3.12" }

      - run: pip install ansible-lint==25.5.0 ansible-core==2.18.1

      - name: ansible-lint --strict --profile production
        working-directory: ansible_collections/student/lab96
        run: ansible-lint --strict --profile production
```

🔍 **Observation** : **`--strict`** élève les warnings au rang d'erreurs. **`--profile production`** active toutes les règles strictes (FQCN, `no-changed-when` sur `command`/`shell`, `mode` quoté, etc.). À combiner avec `tox-ansible` pour matrice plus dynamique.

## 📚 Exercice 6 — Linter le workflow avec `zizmor`

```bash
zizmor .github/workflows/ansible-test.yml
```

Détecte automatiquement :

- Actions non pinnées par SHA.
- `permissions:` trop larges.
- Variables d'env exposées au shell sans escape.
- Absence de `persist-credentials: false`.
- Templates avec `${{ ... }}` injectables.

🔍 **Observation** : **`zizmor`** est l'outil de référence 2026 pour auditer les workflows GitHub. À ajouter en **pre-commit hook** pour bloquer les régressions.

## 📚 Exercice 7 — Équivalent GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - lint
  - sanity
  - units

variables:
  ANSIBLE_VERSIONS: "stable-2.18 stable-2.19 devel"
  PYTHON_VERSIONS: "3.11 3.12"

.collection_setup: &collection_setup
  before_script:
    - pip install "https://github.com/ansible/ansible/archive/${ANSIBLE_VERSION}.tar.gz"
    - mkdir -p ansible_collections/student/lab96
    - shopt -s extglob && cp -r !(ansible_collections) ansible_collections/student/lab96/
    - cd ansible_collections/student/lab96

ansible-lint:
  stage: lint
  image: python:3.12
  script:
    - pip install ansible-lint==25.5.0 ansible-core==2.18.1
    - ansible-lint --strict --profile production

sanity:
  stage: sanity
  image: python:${PYTHON_VERSION}
  parallel:
    matrix:
      - PYTHON_VERSION: ["3.11", "3.12"]
        ANSIBLE_VERSION: ["stable-2.18", "stable-2.19", "devel"]
  <<: *collection_setup
  script:
    - ansible-test sanity --docker default -v --color

units:
  stage: units
  image: python:${PYTHON_VERSION}
  parallel:
    matrix:
      - PYTHON_VERSION: ["3.11", "3.12"]
        ANSIBLE_VERSION: ["stable-2.18", "devel"]
  <<: *collection_setup
  script:
    - ansible-test units --docker default -v --color --python ${PYTHON_VERSION}
```

🔍 **Observation** : **`parallel:matrix`** GitLab CI donne le même effet que la matrice GitHub Actions. **`<<: *collection_setup`** factorise le `before_script` partagé. À combiner avec `rules:` pour ne lancer que sur certains paths modifiés.

## 🔍 Observations à noter

- **Matrice ansible-core × Python** = 4-6 combinaisons typiques.
- **Pinning par SHA** des actions GitHub (40 caractères hex).
- **`permissions: {}`** au global, **`persist-credentials: false`** sur checkout.
- **`ansible-test sanity --docker default`** = validation FQCN + doc + types.
- **`ansible-test units --docker`** = pytest sur les modules Python.
- **`ansible-lint --strict --profile production`** = qualité maximale.
- **Zizmor** lint des workflows.

## 🤔 Questions de réflexion

1. Pourquoi `fail-fast: false` est **recommandé** pour une matrice de tests ?
2. À quoi sert `path: ansible_collections/student/lab96` dans `actions/checkout` ?
3. Comment **bloquer** un pipeline GitLab si **`ansible-test units --coverage`** retombe sous 80 % ?
4. Quel est l'avantage de **`tox-ansible`** vs une matrice GitHub Actions native ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) — écrire un workflow GitHub Actions et un `.gitlab-ci.yml` qui passent **`zizmor`** au vert et exécutent `ansible-test sanity` sur 2 versions ansible-core minimum.

## 💡 Pour aller plus loin

- **Lab 97** : migration rôle standalone → collection.
- **Renovate** pour bumper auto les SHA des actions.
- **`ansible-content-actions`** : composite GitHub Action officielle.
- **`tox-ansible`** : matrice dynamique.

## 🔍 Linter avec `ansible-lint` + `zizmor`

```bash
zizmor labs/collections/ci-tests/challenge/.github/workflows/ansible-test.yml
ansible-lint --profile production labs/collections/ci-tests/
```

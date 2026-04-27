# 🎯 Challenge — Pipeline CI complet pour collection Ansible

## ✅ Objectif

Écrire **deux fichiers de pipeline** (GitHub Actions + GitLab CI) qui passent **`zizmor`** au vert et exécutent `ansible-test sanity` sur **au moins 2 versions** d'ansible-core.

| Élément | Valeur attendue |
| --- | --- |
| Workflow GitHub Actions | `.github/workflows/ansible-test.yml` |
| Pipeline GitLab CI | `.gitlab-ci.yml` |
| Versions ansible-core | au moins **2** (ex: `stable-2.18` + `stable-2.19`) |
| Versions Python | au moins **2** (ex: `3.11` + `3.12`) |
| `permissions: {}` | au niveau workflow |
| `persist-credentials: false` | sur `actions/checkout` |
| Actions pinnées | par **SHA 40 caractères** |

## 🧩 Indices

### Squelette `.github/workflows/ansible-test.yml`

```yaml
name: Ansible test
on:
  push:
    branches: [main]
  pull_request:

permissions: ???                            # ← global = aucune

jobs:
  sanity:
    runs-on: ubuntu-24.04
    permissions:
      contents: ???
    strategy:
      fail-fast: ???
      matrix:
        ansible: [???, ???]                 # ← au moins 2 versions
        python: [???, ???]                  # ← au moins 2 versions
    steps:
      - uses: actions/checkout@???          # ← SHA 40 chars
        with:
          path: ???
          persist-credentials: ???

      - uses: actions/setup-python@???      # ← SHA 40 chars
        with:
          python-version: "${{ matrix.python }}"

      - run: |
          pip install "https://github.com/ansible/ansible/archive/${{ matrix.ansible }}.tar.gz"

      - name: ansible-test sanity
        working-directory: ???
        run: ansible-test sanity --docker default -v --color
```

### Squelette `.gitlab-ci.yml`

```yaml
stages:
  - sanity

sanity:
  stage: sanity
  image: python:${PYTHON_VERSION}
  parallel:
    matrix:
      - PYTHON_VERSION: ["???", "???"]
        ANSIBLE_VERSION: ["???", "???"]
  before_script:
    - pip install "https://github.com/ansible/ansible/archive/${ANSIBLE_VERSION}.tar.gz"
    - mkdir -p ansible_collections/student/lab96
  script:
    - cd ansible_collections/student/lab96
    - ???                                    # ← commande ansible-test
```

> 💡 **Pièges** :
>
> - **`ansible-test`** doit être lancé depuis l'arborescence
>   `ansible_collections/<namespace>/<name>/`. Hors de cet arbre, il
>   refuse.
> - **`ansible-test sanity`** : lint + import + format. Rapide. À
>   lancer en pré-commit.
> - **`ansible-test integration`** : tests réels d'invocation des modules.
>   Demande des cibles (Docker, Podman, AWS…). Plus lourd.
> - **`ansible-test units`** : pytest sur le code Python des modules.
>   Vérifie la logique sans dépendances externes.
> - **Matrix Python** : `--python 3.11`, `3.12`, etc. Vérifier la compat
>   sur les Python ciblés (Ansible 2.18+ exige ≥ 3.11).

## 🚀 Lancement

```bash
# Pas de lancement Ansible (lab structurel CI/CD).
# Validation locale du workflow GitHub Actions :
zizmor labs/collections/ci-tests/challenge/.github/workflows/ansible-test.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/collections/ci-tests/challenge/tests/
```

Le test pytest valide :

- Workflow GitHub Actions présent + actions pinnées par SHA + `permissions: {}` + `persist-credentials: false`.
- Pipeline GitLab CI présent avec stages `sanity` et matrice ansible-core × Python.
- Au moins 2 versions ansible-core dans la matrice.
- Au moins 2 versions Python dans la matrice.

## 🧹 Reset

Lab 100 % structurel — pas de cleanup distant.

## 💡 Pour aller plus loin

- **Renovate** pour bumper auto les SHA des actions.
- **`ansible-content-actions`** : composite officielle.
- **Coverage threshold** : `--coverage --coverage-check`.

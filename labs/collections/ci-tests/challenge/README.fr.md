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

## 🧩 Bloqué ?

```bash
dsoxlab hint collections-ci-tests
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

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

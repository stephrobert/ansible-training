# Votre collection embarque du Python, et c'est là qu'elle cassera

## La situation

Un rôle, c'est du YAML, et le YAML survit assez bien à une montée de version.
Votre collection, elle, embarque un module Python, et il casse sur des choses
qu'un rôle ne remarque jamais : une version de Python qui a retiré un appel de la
bibliothèque standard, un `ansible-core` qui a changé un import de module_utils.
Les utilisateurs le rencontrent, vous non, parce que votre poste ne tourne que sur
une seule combinaison. Et le workflow censé l'attraper utilise des tags flottants
et un token qui a plus de droits que nécessaire.

Votre mission, depuis le répertoire du projet :

1. Croiser les **versions d'`ansible-core` et de Python** dans une matrice, au
   moins deux de chaque, pour tester les combinaisons que vos utilisateurs vivent.
2. Lancer les **tests de sanity et les tests unitaires** de la collection en
   conteneur, pour que le verdict ne dépende pas de ce qui traîne sur le runner.
3. Durcir le workflow lui-même : **aucune permission globale**, chaque job ne
   recevant que son strict nécessaire, et **aucun identifiant laissé** derrière le
   checkout.
4. **Épingler chaque action tierce par SHA de commit** : un tag peut être déplacé
   sous vos pieds, et un linter supply-chain vous le dira.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/pipeline-ci/

## 🎯 Challenge — Pipeline CI complet pour collection Ansible

### ✅ Objectif

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

### 🧩 Bloqué ?

```bash
dsoxlab hint collections-ci-tests
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

```bash
# Pas de lancement Ansible (lab structurel CI/CD).
# Validation locale du workflow GitHub Actions :
zizmor labs/collections/ci-tests/challenge/.github/workflows/ansible-test.yml
```

### 🧪 Validation automatisée

```bash
pytest -v labs/collections/ci-tests/challenge/tests/
```

Le test pytest valide :

- Workflow GitHub Actions présent + actions pinnées par SHA + `permissions: {}` + `persist-credentials: false`.
- Pipeline GitLab CI présent avec stages `sanity` et matrice ansible-core × Python.
- Au moins 2 versions ansible-core dans la matrice.
- Au moins 2 versions Python dans la matrice.

### 🧹 Reset

Lab 100 % structurel — pas de cleanup distant.

### 💡 Pour aller plus loin

- **Renovate** pour bumper auto les SHA des actions.
- **`ansible-content-actions`** : composite officielle.
- **Coverage threshold** : `--coverage --coverage-check`.

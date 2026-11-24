# Le rôle est public, des inconnus vont proposer des patches

## La situation

Votre rôle `webserver` est open source. La première contribution extérieure
arrive demain, et vous ne la jouerez pas à la main : vous n'avez ni confiance
dans ce code ni le temps, et personne ne veut être celui qui a oublié de tester
une distribution. Pire : un workflow qui clone le dépôt et exécute du code non
vérifié avec un token en écriture, c'est ainsi qu'un rôle devient un vecteur
d'attaque. La barrière doit être automatique, et sûre même sur la branche d'un
contributeur.

Votre mission, depuis le répertoire du projet :

1. Faire passer chaque push et chaque merge request par **deux barrières** : le
   lint d'abord, le cycle Molecule ensuite, pour qu'une faute de style ne brûle
   jamais des minutes de matrice.
2. Décliner le job de test sur une matrice **distributions x versions
   d'`ansible-core`**, jouée en parallèle.
3. Mettre en cache l'installation des dépendances Python, pour que le pipeline
   reste assez rapide pour qu'on l'attende vraiment.
4. Verrouiller le workflow : **permissions minimales** sur le token, et aucun
   identifiant laissé derrière le checkout pour les étapes suivantes.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ci-github-actions/

## 🎯 Challenge : écrire le workflow GitHub Actions (lint + matrice Molecule)

### ✅ Mission

Le fichier `.github/workflows/test.yml` est livré **incomplet** (des `???`
et des jobs vides). Complétez-le pour obtenir une CI de rôle Ansible
conforme à l'état attendu ci-dessous. C'est vous qui écrivez le workflow :
aucun modèle prêt à copier n'est fourni.

État attendu (c'est ce que pytest vérifie) :

| Exigence | Détail |
| --- | --- |
| 2 jobs | `lint` puis `molecule`, chaîné par `needs:` |
| Lint | `yamllint` et `ansible-lint --profile=production` exécutés dans le job `lint` |
| Matrice | `strategy.matrix` avec `distro` (au moins 2 images) et `ansible` (au moins 2 versions d'ansible-core) |
| Rapport complet | `fail-fast: false` sur la matrice : une combinaison qui échoue n'annule pas les autres |
| Sécurité supply chain | toutes les actions `uses:` épinglées par SHA de 40 caractères |
| Moindre privilège | `permissions:` global vide (`{}`), droits accordés job par job |
| Credentials | `persist-credentials: false` sur chaque `actions/checkout` |

### 🧩 Bloqué ?

```bash
dsoxlab hint ci-github-actions
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 📓 Journal de commandes

Quand votre workflow est prêt, consignez dans `challenge/solution.sh` les
commandes que vous avez utilisées pour le construire et le valider (par
exemple les appels `gh api` et `actionlint`). Ce journal, exigé par le
harnais de tests, doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/ci/github-actions/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ci-github-actions
```

### 💡 Pour aller plus loin

- `zizmor .github/workflows/test.yml` : audit sécurité statique des workflows.
- Reusable workflows : mutualiser cette CI entre plusieurs rôles.
- Dependabot : PR automatiques pour faire suivre les SHA épinglés.

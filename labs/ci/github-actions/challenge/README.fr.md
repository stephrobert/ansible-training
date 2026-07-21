# 🎯 Challenge : écrire le workflow GitHub Actions (lint + matrice Molecule)

## ✅ Mission

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

## 🧩 Indices

- Un tag (`@v4`) peut être déplacé, un SHA non. Pour trouver le SHA d'un tag :

  ```bash
  gh api repos/actions/checkout/git/refs/tags/v4.2.2 --jq .object.sha
  ```

- `permissions: {}` au global ne suffit pas à builder : réélargissez dans
  chaque job (`contents: read` au minimum).
- La matrice se déclare sous `strategy.matrix`, et `fail-fast: false`
  laisse toutes les combinaisons s'exécuter même si l'une échoue.
- Validez localement avec `actionlint .github/workflows/test.yml` : pytest
  le lance aussi si le binaire est présent.

## 📓 Journal de commandes

Quand votre workflow est prêt, consignez dans `challenge/solution.sh` les
commandes que vous avez utilisées pour le construire et le valider (par
exemple les appels `gh api` et `actionlint`). Ce journal, exigé par le
harnais de tests, doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/ci/github-actions/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ci-github-actions
```

## 💡 Pour aller plus loin

- `zizmor .github/workflows/test.yml` : audit sécurité statique des workflows.
- Reusable workflows : mutualiser cette CI entre plusieurs rôles.
- Dependabot : PR automatiques pour faire suivre les SHA épinglés.

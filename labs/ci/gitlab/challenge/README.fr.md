# 🎯 Challenge : écrire le pipeline GitLab CI (lint + matrice + release)

## ✅ Mission

Le fichier `.gitlab-ci.yml` est livré **incomplet** (des `???` et des jobs
manquants). Complétez-le pour obtenir le pipeline attendu : c'est vous qui
écrivez chaque job, aucun modèle prêt à copier n'est fourni.

État attendu (c'est ce que pytest vérifie) :

| Exigence | Détail |
| --- | --- |
| Stages | `lint`, `test` et `release` déclarés dans `stages:` |
| Job `ansible-lint` | stage `lint`, exécute `yamllint` et `ansible-lint --profile=production` |
| Job `molecule-test` | stage `test`, `needs: ["ansible-lint"]`, `parallel:matrix` d'au moins 3 combinaisons DISTRO x ANSIBLE_VERSION |
| Job `release` | stage `release`, `rules:` avec une condition sur `$CI_COMMIT_TAG` (déclenché uniquement sur tag) |
| Secrets | aucun token ni mot de passe en clair dans le fichier |

## 🧩 Indices

- La matrice GitLab se déclare ainsi :

  ```yaml
  parallel:
    matrix:
      - DISTRO: ...
        ANSIBLE_VERSION: "..."
  ```

  Chaque entrée de la liste est une combinaison (ou un produit cartésien si
  une clé porte une liste).

- `needs: ["ansible-lint"]` court-circuite l'ordre des stages et documente la
  dépendance réelle.
- Pour la release, le pattern canonique est :

  ```yaml
  rules:
    - if: $CI_COMMIT_TAG
  ```

- Le token Galaxy ne se met JAMAIS ici : Settings, CI/CD, Variables
  (masked + protected), puis référence `$GALAXY_API_KEY` dans le script.

## 📓 Journal de commandes

Quand votre pipeline est prêt, consignez dans `challenge/solution.sh` les
commandes utilisées pour le valider localement (par exemple
`python3 -c "import yaml; yaml.safe_load(open('.gitlab-ci.yml'))"` ou un
run `gitlab-ci-local`). Ce journal doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/ci/gitlab/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ci-gitlab
```

## 💡 Pour aller plus loin

- `gitlab-ci-local` : exécuter le pipeline sur votre poste avant de pousser.
- `include:` : factoriser ce pipeline dans un repo de templates CI.
- Badges de pipeline et de couverture dans le README du rôle.

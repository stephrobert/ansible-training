# L'entreprise tourne sur GitLab, et une release vient de partir d'une branche

## La situation

Les rôles de l'équipe ont migré sur le GitLab interne, et l'ancien workflow
GitHub ne se traduit pas. La première tentative a empiré les choses : le job de
publication n'avait aucune condition, et un merge sur une branche de feature a
poussé sur Galaxy une release que personne n'avait validée. Publier n'est pas une
étape d'un pipeline de test. C'est ce qui arrive quand quelqu'un, et seulement
quand quelqu'un, pose délibérément un tag de version.

Votre mission, depuis le répertoire du projet :

1. Découper le pipeline en **trois stages**, lint puis test puis release, pour
   qu'aucun job ne s'exécute avant celui qui aurait pu l'arrêter.
2. Décliner le stage de test sur une **matrice distributions et versions**, en
   parallèle, et mettre les dépendances Python en cache entre les runs.
3. Conditionner le job de release pour qu'il ne se déclenche **que sur un tag
   Git** : jamais sur un push de branche, jamais sur une merge request.
4. Faire publier ce job sur Galaxy avec son token, et tenir ce token hors de
   portée de tous les autres stages.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ci-gitlab/

## 🎯 Challenge : écrire le pipeline GitLab CI (lint + matrice + release)

### ✅ Mission

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

### 🧩 Bloqué ?

```bash
dsoxlab hint ci-gitlab
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 📓 Journal de commandes

Quand votre pipeline est prêt, consignez dans `challenge/solution.sh` les
commandes utilisées pour le valider localement (par exemple
`python3 -c "import yaml; yaml.safe_load(open('.gitlab-ci.yml'))"` ou un
run `gitlab-ci-local`). Ce journal doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/ci/gitlab/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ci-gitlab
```

### 💡 Pour aller plus loin

- `gitlab-ci-local` : exécuter le pipeline sur votre poste avant de pousser.
- `include:` : factoriser ce pipeline dans un repo de templates CI.
- Badges de pipeline et de couverture dans le README du rôle.

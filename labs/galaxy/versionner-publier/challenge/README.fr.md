# Vous avez renommé une variable et cassé quatre équipes

## La situation

Votre rôle `webserver` est utilisé dans toute l'entreprise. À la dernière
release, vous avez renommé une variable d'entrée, livré ça en correctif, et quatre
projets ont cassé au run suivant. Ils n'avaient rien fait de mal : ils épinglaient
une plage de patch, parce qu'un patch est censé être sans risque. La casse était
réelle, mais le mensonge était dans le numéro de version. Un consommateur ne peut
pas épingler sainement si la numérotation du publieur ne veut rien dire.

Votre mission, depuis le répertoire du projet :

1. Poser la règle : **quel chiffre bouge** et quand. Ce qui impose une majeure, ce
   qui mérite une mineure, ce qui est vraiment un correctif, et où tombe un
   renommage.
2. Tenir un **changelog** exploitable, classé par version et par nature de
   changement, pour qu'un lecteur sache en dix secondes si la montée fait mal.
3. Poser la release en **tag Git annoté**, et documenter la procédure pour
   qu'elle soit reproductible par quelqu'un d'autre que vous.
4. Automatiser la publication depuis la CI sur ce tag, et documenter comment le
   **consommateur** doit épingler le résultat.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/versionner-publier/

## 🎯 Challenge : versionner et préparer une publication, pour de vrai

### ✅ Mission

Fini le versionnement sur papier : vous écrivez un script
`challenge/solution.sh` qui **pratique** le workflow de release dans
`challenge/work/`, et pytest **exécute votre script** puis vérifie l'état
Git et les artefacts produits. Tout est local, aucun compte Galaxy requis.

Votre script, lancé depuis la racine du lab, doit construire :

| Effet attendu | Détail |
| --- | --- |
| `challenge/work/repo/` | un dépôt Git initialisé contenant le rôle `webserver` (copié depuis `roles/`) et un `CHANGELOG.md`, le tout commité |
| `CHANGELOG.md` | format Keep a Changelog : au moins 2 versions `[X.Y.Z]`, section `### Added`, et `### Changed` ou `### Fixed` |
| Tag Git | un tag **annoté** `vX.Y.Z` dont la version correspond à la **dernière** entrée du CHANGELOG |
| `challenge/work/dist/` | l'archive d'une collection `acme.webstack` buildée avec `ansible-galaxy collection build`, dont la version de `galaxy.yml` est **la même** que le tag |

Contraintes :

- Script **rejouable** : pytest supprime `challenge/work/` avant de
  l'exécuter, votre script recrée tout.
- `set -euo pipefail` en tête.
- Le contenu du CHANGELOG est le vôtre : décrivez de vraies évolutions du
  rôle webserver (pytest vérifie le format et la cohérence des versions,
  pas la prose).

### 🧩 Bloqué ?

```bash
dsoxlab hint galaxy-versionner-publier
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🧪 Validation

```bash
chmod +x challenge/solution.sh
pytest -v labs/galaxy/versionner-publier/challenge/tests/
```

Pytest exécute votre script, interroge réellement Git (`git tag`,
`git cat-file`, `git log`) et contrôle l'archive buildée.

### 🧹 Reset

```bash
dsoxlab clean galaxy-versionner-publier
```

### 💡 Pour aller plus loin

- `PUBLISH.md` (à la racine du lab) : la procédure de publication Galaxy
  complète, webhook GitHub inclus.
- `towncrier` : générer le CHANGELOG depuis des fragments de PR.
- Workflow GitHub `on: push: tags: ['v*']` qui publie sur Galaxy (lab 69).

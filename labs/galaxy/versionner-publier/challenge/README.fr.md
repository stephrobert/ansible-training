# 🎯 Challenge : versionner et préparer une publication, pour de vrai

## ✅ Mission

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

## 🧩 Bloqué ?

```bash
dsoxlab hint galaxy-versionner-publier
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🧪 Validation

```bash
chmod +x challenge/solution.sh
pytest -v labs/galaxy/versionner-publier/challenge/tests/
```

Pytest exécute votre script, interroge réellement Git (`git tag`,
`git cat-file`, `git log`) et contrôle l'archive buildée.

## 🧹 Reset

```bash
dsoxlab clean galaxy-versionner-publier
```

## 💡 Pour aller plus loin

- `PUBLISH.md` (à la racine du lab) : la procédure de publication Galaxy
  complète, webhook GitHub inclus.
- `towncrier` : générer le CHANGELOG depuis des fragments de PR.
- Workflow GitHub `on: push: tags: ['v*']` qui publie sur Galaxy (lab 69).

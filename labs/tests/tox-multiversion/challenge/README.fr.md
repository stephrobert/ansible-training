# 🎯 Challenge : écrire le tox.ini multi-versions

## ✅ Mission

Le fichier `tox.ini` est livré en **squelette**. Écrivez la configuration
qui teste le rôle `webserver` sur plusieurs versions d'ansible-core.

État attendu (c'est ce que pytest vérifie) :

| Élément | Attente |
| --- | --- |
| `[tox] envlist` | syntaxe range `ansible-2.{...}` couvrant au moins 3 versions récentes d'ansible-core |
| `[testenv]` | `commands` lance `molecule test` |
| `[testenv:ansible-X]` | au moins 3 sections, chacune épinglant `ansible-core` dans ses `deps` |
| `[testenv:lint]` | environnement séparé pour yamllint + ansible-lint (fail-fast, sans monter d'instance) |

## 🧩 Bloqué ?

```bash
dsoxlab hint tests-tox-multiversion
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 📓 Journal de commandes

Quand votre configuration est prête, consignez dans `challenge/solution.sh`
les commandes tox exécutées. Ce journal doit exister pour que pytest
s'exécute :

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/tests/tox-multiversion/challenge/tests/
```

Le test parse votre tox.ini (sémantique des sections) et, si tox est
installé sur le poste, exécute `tox --listenvs` pour prouver que la
configuration est acceptée par l'outil.

## 🧹 Reset

```bash
dsoxlab clean tests-tox-multiversion
```

## 💡 Pour aller plus loin

- `tox -p auto` : exécuter les environnements en parallèle.
- `tox-uv` : résolution des deps beaucoup plus rapide.
- Croiser avec la matrice CI du lab 69 : tox local, matrice GitHub distante.

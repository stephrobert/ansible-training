# 🎯 Challenge : mettre un rôle au niveau du profil production

## ✅ Mission

Le rôle `roles/webserver` est livré **volontairement fautif** : il
fonctionne, mais `ansible-lint --profile production` y relève une bonne
dizaine de violations (FQCN manquants, tâche sans nom, mode octal risqué,
`ignore_errors`, `shell` à la place d'un module...). Les fichiers de
configuration lint sont livrés en squelette.

Votre travail, en deux temps :

1. **Écrire la configuration** : `.ansible-lint` (profil production,
   exclusions), `.yamllint` (truthy strict), `.pre-commit-config.yaml`
   (hooks de base + yamllint + ansible-lint).
2. **Corriger le rôle** jusqu'à ce que `ansible-lint --profile production
   roles/` retourne 0, **sans changer son comportement** (mêmes paquets,
   même service, même page déployée).

Pytest exécute réellement `ansible-lint --profile production` : le lab
n'est validé que quand le linter est vert.

## 🧩 Bloqué ?

```bash
dsoxlab hint tests-ansible-lint-production
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 📓 Journal de commandes

Quand tout est vert, consignez dans `challenge/solution.sh` les commandes
exécutées (`ansible-lint ...`, `yamllint roles/`, `pre-commit run
--all-files`). Ce journal doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/tests/ansible-lint-production/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean tests-ansible-lint-production
```

## 💡 Pour aller plus loin

- `pre-commit install` : rendre le commit impossible tant que le lint échoue.
- `ansible-lint --fix` : corrections automatiques (à relire avant commit).
- Brancher ce même profil dans la CI du lab 69.

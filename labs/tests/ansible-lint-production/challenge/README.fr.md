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

## 🧩 Indices

- Lancez le linter et traitez les findings un par un :

  ```bash
  cd labs/tests/ansible-lint-production/
  ansible-lint --profile production roles/
  ```

- Chaque identifiant de règle (fqcn[action-core], risky-octal,
  no-changed-when...) a sa page : https://docs.ansible.com/projects/lint/rules/
- « Sans changer le comportement » : remplacer `shell: systemctl ...` par
  le module idoine, pas supprimer la tâche. Pytest vérifie que le rôle
  installe toujours nginx, déploie toujours la page et gère toujours le
  service.
- Pour `.yamllint`, ansible-lint affiche en tête de run les exigences de
  compatibilité qu'il attend d'une config custom : lisez ce warning.

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

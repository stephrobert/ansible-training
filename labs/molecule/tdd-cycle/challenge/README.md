# 🎯 Challenge — Cycle TDD complet

## ✅ Objectif

Démontrer un cycle TDD valide sur le rôle `users` :

| Élément | Présence requise |
| --- | --- |
| Rôle `roles/users/{tasks,defaults,meta}` | ✅ |
| `meta/argument_specs.yml` avec `users_to_create` | ✅ |
| `verify.yml` avec **≥ 4** assertions distinctes | ✅ |
| `converge.yml` qui crée alice avec `/bin/zsh` | ✅ |
| `tasks/main.yml` qui boucle sur `users_to_create` | ✅ |

## 🧩 Indices

C'est un challenge structurel — les fichiers du rôle et du scénario
Molecule sont déjà livrés. Vérifiez-les puis posez le `solution.sh` minimal :

```bash
echo "Lab 64 : cycle TDD validé par pytest." > challenge/solution.sh
chmod +x challenge/solution.sh
```

## 🚀 Lancement (optionnel)

```bash
cd labs/molecule/tdd-cycle && molecule test
```

## 🧪 Validation

```bash
pytest -v labs/molecule/tdd-cycle/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/molecule/tdd-cycle clean
```

## 💡 Pour aller plus loin

- **`ansible-lint --profile production`** : validez la qualité de votre solution.

  ```bash
  ansible-lint --profile production labs/molecule/tdd-cycle/challenge/solution.yml
  ```

  Sortie attendue : `Passed: 0 failure(s), 0 warning(s)`.

- **Idempotence** : relancez la solution une seconde fois — un `PLAY RECAP`
  avec `changed=0` partout confirme un playbook propre.

- **Cas limites** : pensez aux scénarios d'erreur (host indisponible,
  dépendance manquante, valeur invalide) que votre solution pourrait
  rencontrer en production. Comment les gérer (`block/rescue`,
  `failed_when`, `assert`) ?

# 🎯 Challenge — Configuration Molecule enrichie

## ✅ Objectif

Vérifier que le scénario Molecule du lab est **enrichi** par rapport au
minimum (lab 62) :

| Fichier | Présence |
| --- | --- |
| `molecule/default/prepare.yml` | ✅ |
| `molecule/default/requirements.yml` | ✅ |
| `molecule/default/molecule.yml` avec `host_vars` | ✅ |
| `molecule/default/molecule.yml` avec `test_sequence` incluant `idempotence` et `verify` | ✅ |
| Callbacks `profile_tasks` activés | ✅ |

## 🧩 Indices

C'est un challenge **purement structurel** — les fichiers sont déjà livrés
dans `molecule/default/`. Le challenge consiste à :

1. Lire et comprendre les enrichissements.
2. Optionnellement lancer `molecule test` pour voir l'effet (callbacks,
   idempotence forcée).

Posez un `solution.sh` minimal :

```bash
#!/usr/bin/env bash
echo "Lab 63 : config Molecule enrichie validée par pytest."
exit 0
```

## 🚀 Lancement (optionnel)

```bash
cd labs/molecule/installation-config && molecule test
```

## 🧪 Validation automatisée

```bash
pytest -v labs/molecule/installation-config/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/molecule/installation-config clean
```

## 💡 Pour aller plus loin

- **`ansible-lint --profile production`** : validez la qualité de votre solution.

  ```bash
  ansible-lint --profile production labs/molecule/installation-config/challenge/solution.yml
  ```

  Sortie attendue : `Passed: 0 failure(s), 0 warning(s)`.

- **Idempotence** : relancez la solution une seconde fois — un `PLAY RECAP`
  avec `changed=0` partout confirme un playbook propre.

- **Cas limites** : pensez aux scénarios d'erreur (host indisponible,
  dépendance manquante, valeur invalide) que votre solution pourrait
  rencontrer en production. Comment les gérer (`block/rescue`,
  `failed_when`, `assert`) ?

# 🎯 Challenge — Workflow GitHub Actions complet (lint + matrix molecule)

## ✅ Objectif

Le test pytest valide la structure du fichier CI livré dans le lab :
**Workflow GitHub Actions complet (lint + matrix molecule)**.

## 🧩 Indices

C'est un challenge structurel. Posez `solution.sh` minimal :

```bash
echo "Lab 69 : Workflow GitHub Actions complet (lint + matrix molecule) validé par pytest." > challenge/solution.sh
chmod +x challenge/solution.sh
```

## 🚀 Lancement (optionnel)

```bash
# Local : exécuter avec act
act -W labs/ci/github-actions/.github/workflows/test.yml

# Cloud : push sur GitHub → workflow automatique
```

## 🧪 Validation

```bash
pytest -v labs/ci/github-actions/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ci/github-actions/ clean
```

## 💡 Pour aller plus loin

- **`ansible-lint --profile production`** : validez la qualité de votre solution.

  ```bash
  ansible-lint --profile production labs/ci/github-actions/challenge/solution.yml
  ```

  Sortie attendue : `Passed: 0 failure(s), 0 warning(s)`.

- **Idempotence** : relancez la solution une seconde fois — un `PLAY RECAP`
  avec `changed=0` partout confirme un playbook propre.

- **Cas limites** : pensez aux scénarios d'erreur (host indisponible,
  dépendance manquante, valeur invalide) que votre solution pourrait
  rencontrer en production. Comment les gérer (`block/rescue`,
  `failed_when`, `assert`) ?

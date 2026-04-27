# 🎯 Challenge — Pipeline GitLab CI (lint + parallel matrix + release Galaxy)

## ✅ Objectif

Le test pytest valide la structure du fichier CI livré dans le lab :
**Pipeline GitLab CI (lint + parallel matrix + release Galaxy)**.

## 🧩 Indices

C'est un challenge structurel. Posez `solution.sh` minimal :

```bash
echo "Lab 70 : Pipeline GitLab CI (lint + parallel matrix + release Galaxy) validé par pytest." > challenge/solution.sh
chmod +x challenge/solution.sh
```

## 🚀 Lancement (optionnel)

```bash
# Local : valider la syntaxe avec gitlab-ci-local
gitlab-ci-local --file labs/ci/gitlab/.gitlab-ci.yml

# Cloud : push sur GitLab → pipeline automatique
```

## 🧪 Validation

```bash
pytest -v labs/ci/gitlab/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ci/gitlab/ clean
```

## 💡 Pour aller plus loin

- **`ansible-lint --profile production`** : validez la qualité de votre solution.

  ```bash
  ansible-lint --profile production labs/ci/gitlab/challenge/solution.yml
  ```

  Sortie attendue : `Passed: 0 failure(s), 0 warning(s)`.

- **Idempotence** : relancez la solution une seconde fois — un `PLAY RECAP`
  avec `changed=0` partout confirme un playbook propre.

- **Cas limites** : pensez aux scénarios d'erreur (host indisponible,
  dépendance manquante, valeur invalide) que votre solution pourrait
  rencontrer en production. Comment les gérer (`block/rescue`,
  `failed_when`, `assert`) ?

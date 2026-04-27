# 🎯 Challenge — Tester avec testinfra (verifier Python)

## ✅ Objectif

Le test pytest valide la **structure** des fichiers livrés dans ce lab :

- Lab 66 : Tester avec testinfra (verifier Python).

## 🧩 Indices

C'est un challenge structurel. Posez `solution.sh` minimal :

```bash
echo "Lab 66 : Tester avec testinfra (verifier Python) validé par pytest." > challenge/solution.sh
chmod +x challenge/solution.sh
```

## 🚀 Lancement (optionnel)

```bash
cd labs/tests/testinfra/ && molecule test
```

Verify utilise désormais testinfra (Python) au lieu d'ansible (YAML).

## 🧪 Validation

```bash
pytest -v labs/tests/testinfra/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/tests/testinfra/ clean
```

## 💡 Pour aller plus loin

- **`ansible-lint --profile production`** : validez la qualité de votre solution.

  ```bash
  ansible-lint --profile production labs/tests/testinfra/challenge/solution.yml
  ```

  Sortie attendue : `Passed: 0 failure(s), 0 warning(s)`.

- **Idempotence** : relancez la solution une seconde fois — un `PLAY RECAP`
  avec `changed=0` partout confirme un playbook propre.

- **Cas limites** : pensez aux scénarios d'erreur (host indisponible,
  dépendance manquante, valeur invalide) que votre solution pourrait
  rencontrer en production. Comment les gérer (`block/rescue`,
  `failed_when`, `assert`) ?

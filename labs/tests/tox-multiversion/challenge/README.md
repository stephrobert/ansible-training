# 🎯 Challenge — Tester sur 3 versions d'Ansible avec tox

## ✅ Objectif

Le test pytest valide la **structure** des fichiers livrés dans ce lab :

- Lab 67 : Tester sur 3 versions d'Ansible avec tox.

## 🧩 Indices

C'est un challenge structurel. Posez `solution.sh` minimal :

```bash
echo "Lab 67 : Tester sur 3 versions d'Ansible avec tox validé par pytest." > challenge/solution.sh
chmod +x challenge/solution.sh
```

## 🚀 Lancement (optionnel)

```bash
cd labs/tests/tox-multiversion/ && tox -e ansible-2.18      # une version
cd labs/tests/tox-multiversion/ && tox                       # toutes les versions
```

## 🧪 Validation

```bash
pytest -v labs/tests/tox-multiversion/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/tests/tox-multiversion/ clean
```

## 💡 Pour aller plus loin

- **`ansible-lint --profile production`** : validez la qualité de votre solution.

  ```bash
  ansible-lint --profile production labs/tests/tox-multiversion/challenge/solution.yml
  ```

  Sortie attendue : `Passed: 0 failure(s), 0 warning(s)`.

- **Idempotence** : relancez la solution une seconde fois — un `PLAY RECAP`
  avec `changed=0` partout confirme un playbook propre.

- **Cas limites** : pensez aux scénarios d'erreur (host indisponible,
  dépendance manquante, valeur invalide) que votre solution pourrait
  rencontrer en production. Comment les gérer (`block/rescue`,
  `failed_when`, `assert`) ?

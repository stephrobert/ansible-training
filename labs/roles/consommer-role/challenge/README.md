# 🎯 Challenge — 3 patterns de consommation d'un rôle (roles:, import_role, include_role)

## ✅ Objectif

Le test pytest valide la structure des fichiers livrés. Pour ce lab :
**3 patterns de consommation d'un rôle (roles:, import_role, include_role)**.

## 🧩 Indices

C'est un challenge structurel — les fichiers sont déjà livrés. Posez
`solution.sh` minimal :

```bash
echo "Lab 71 : 3 patterns de consommation d'un rôle (roles:, import_role, include_role) validé par pytest." > challenge/solution.sh
chmod +x challenge/solution.sh
```

## 🚀 Lancement

```bash
ansible-playbook labs/roles/consommer-role/playbook.yml
```

## 🧪 Validation

```bash
pytest -v labs/roles/consommer-role/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/roles/consommer-role/ clean
```

## 💡 Pour aller plus loin

- **`ansible-lint --profile production`** : validez la qualité de votre solution.

  ```bash
  ansible-lint --profile production labs/roles/consommer-role/challenge/solution.yml
  ```

  Sortie attendue : `Passed: 0 failure(s), 0 warning(s)`.

- **Idempotence** : relancez la solution une seconde fois — un `PLAY RECAP`
  avec `changed=0` partout confirme un playbook propre.

- **Cas limites** : pensez aux scénarios d'erreur (host indisponible,
  dépendance manquante, valeur invalide) que votre solution pourrait
  rencontrer en production. Comment les gérer (`block/rescue`,
  `failed_when`, `assert`) ?

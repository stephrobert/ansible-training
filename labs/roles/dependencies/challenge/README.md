# 🎯 Challenge — Rôle webserver avec 2 dépendances (selinux_setup + firewall_setup)

## ✅ Objectif

Le test pytest valide la structure des fichiers livrés. Pour ce lab :
**Rôle webserver avec 2 dépendances (selinux_setup + firewall_setup)**.

## 🧩 Indices

C'est un challenge structurel — les fichiers sont déjà livrés. Posez
`solution.sh` minimal :

```bash
echo "Lab 72 : Rôle webserver avec 2 dépendances (selinux_setup + firewall_setup) validé par pytest." > challenge/solution.sh
chmod +x challenge/solution.sh
```

## 🚀 Lancement

```bash
ansible-playbook labs/roles/dependencies/playbook.yml
```

## 🧪 Validation

```bash
pytest -v labs/roles/dependencies/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/roles/dependencies/ clean
```

## 💡 Pour aller plus loin

- **`ansible-lint --profile production`** : validez la qualité de votre solution.

  ```bash
  ansible-lint --profile production labs/roles/dependencies/challenge/solution.yml
  ```

  Sortie attendue : `Passed: 0 failure(s), 0 warning(s)`.

- **Idempotence** : relancez la solution une seconde fois — un `PLAY RECAP`
  avec `changed=0` partout confirme un playbook propre.

- **Cas limites** : pensez aux scénarios d'erreur (host indisponible,
  dépendance manquante, valeur invalide) que votre solution pourrait
  rencontrer en production. Comment les gérer (`block/rescue`,
  `failed_when`, `assert`) ?

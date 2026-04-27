# 🎯 Challenge — Multi-distro avec Molecule

## ✅ Objectif

Vérifier que le rôle `webserver` est portable :

- `vars/RedHat.yml` ET `vars/Debian.yml` présents avec des **valeurs
  divergentes** (HTML dir, user).
- `tasks/main.yml` utilise `ansible.builtin.package:` (pas `dnf:` ni `apt:`).
- `tasks/main.yml` utilise `include_vars` avec `ansible_os_family`.
- `molecule.yml` déclare **≥ 3 plateformes**.

## 🧩 Indices

Tout le rôle et le scénario Molecule sont déjà livrés. Lisez-les puis
posez `solution.sh` minimal :

```bash
echo "Lab 65 : multi-distro validé par pytest." > challenge/solution.sh
chmod +x challenge/solution.sh
```

## 🚀 Lancement (optionnel — nécessite Podman/Docker)

```bash
cd labs/molecule/scenarios-multi-distro && molecule test
```

Vous verrez 3 instances en parallèle (RHEL + Debian + Ubuntu) avec le
même rôle qui s'adapte à chaque OS.

## 🧪 Validation

```bash
pytest -v labs/molecule/scenarios-multi-distro/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/molecule/scenarios-multi-distro clean
```

## 💡 Pour aller plus loin

- **`ansible-lint --profile production`** : validez la qualité de votre solution.

  ```bash
  ansible-lint --profile production labs/molecule/scenarios-multi-distro/challenge/solution.yml
  ```

  Sortie attendue : `Passed: 0 failure(s), 0 warning(s)`.

- **Idempotence** : relancez la solution une seconde fois — un `PLAY RECAP`
  avec `changed=0` partout confirme un playbook propre.

- **Cas limites** : pensez aux scénarios d'erreur (host indisponible,
  dépendance manquante, valeur invalide) que votre solution pourrait
  rencontrer en production. Comment les gérer (`block/rescue`,
  `failed_when`, `assert`) ?

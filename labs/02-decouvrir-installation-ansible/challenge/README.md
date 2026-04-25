# 🎯 Challenge — Script de vérification d'installation

## ✅ Objectif

Écrire un script Bash `solution.sh` à la racine de **ce répertoire**
(`labs/02-decouvrir-installation-ansible/challenge/solution.sh`) qui :

1. Vérifie que **`ansible --version`** retourne `core 2.18` ou supérieur
2. Vérifie que les **8 binaires standard** sont dans le `PATH`
3. Vérifie qu'au moins **100 modules** sont disponibles via `ansible-doc -l`
4. Vérifie que les **3 collections clés** sont installées :
   `ansible.posix`, `community.general`, `community.libvirt`
5. **Exit 0** si tout est OK, **exit 1** sinon avec un message d'erreur clair

Indices :

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. Version
ANSIBLE_VERSION=$(ansible --version | head -1 | grep -oE 'core [0-9]+\.[0-9]+' | awk '{print $2}')
MAJOR=$(echo "$ANSIBLE_VERSION" | cut -d. -f1)
MINOR=$(echo "$ANSIBLE_VERSION" | cut -d. -f2)
if [[ $MAJOR -lt 2 || ( $MAJOR -eq 2 && $MINOR -lt 18 ) ]]; then
  echo "FAIL : ansible-core $ANSIBLE_VERSION < 2.18" >&2
  exit 1
fi

# Suite des checks ...
```

## 🧪 Validation

Le script `tests/test_install.py` lance votre `solution.sh` et vérifie
qu'il retourne **exit 0** sans erreur :

```bash
pytest -v labs/02-decouvrir-installation-ansible/challenge/tests/
```

## 🚀 Pour aller plus loin

- Ajoutez un check de la **version Python** (≥ 3.11 attendu).
- Affichez la **méthode d'installation détectée** (pipx vs dnf vs mise) en
  parsant `ansible --version`.

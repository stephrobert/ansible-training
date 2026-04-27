# 🎯 Challenge — Script de vérification d'installation

## ✅ Objectif

Écrire un script Bash `solution.sh` à la racine de **ce répertoire**
(`labs/decouvrir/installation-ansible/challenge/solution.sh`) qui :

1. Vérifie que **`ansible --version`** retourne `core 2.18` ou supérieur
2. Vérifie que les **8 binaires standard** sont dans le `PATH`
3. Vérifie qu'au moins **100 modules** sont disponibles via `ansible-doc -l`
4. Vérifie que les **3 collections clés** sont installées :
   `ansible.posix`, `community.general`, `community.libvirt`
5. **Exit 0** si tout est OK, **exit 1** sinon avec un message d'erreur clair

Squelette à compléter :

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. Récupérer la version d'ansible-core (ex. : "2.18")
#    Astuce : `ansible --version | head -1` retourne "ansible [core 2.x.y]".
VERSION=$(ansible --version | ???)
# Comparer "$VERSION" à 2.18 — sortir avec exit 1 si inférieur.

# 2. Vérifier la présence des 8 binaires standard dans le PATH.
#    Liste : ansible, ansible-playbook, ansible-doc, ansible-galaxy,
#            ansible-vault, ansible-inventory, ansible-config, ansible-console.
for bin in ???; do
    command -v "$bin" >/dev/null || { echo "MISSING $bin"; exit 1; }
done

# 3. Compter les modules disponibles via `ansible-doc -l` (>= 100 attendu).
COUNT=$(ansible-doc -l 2>/dev/null | wc -l)
[[ ??? ]] || { echo "Trop peu de modules ($COUNT)"; exit 1; }

# 4. Vérifier la présence des 3 collections clés via `ansible-galaxy collection list`.
for col in ansible.posix community.general community.libvirt; do
    ansible-galaxy collection list "$col" >/dev/null 2>&1 \
        || { echo "Collection $col manquante"; exit 1; }
done

echo "Installation OK"
```

## 🧪 Validation

Le script `tests/test_install.py` lance votre `solution.sh` et vérifie
qu'il retourne **exit 0** sans erreur :

```bash
pytest -v labs/decouvrir/installation-ansible/challenge/tests/
```

## 🚀 Pour aller plus loin

- Ajoutez un check de la **version Python** (≥ 3.11 attendu).
- Affichez la **méthode d'installation détectée** (pipx vs dnf vs mise) en
  parsant `ansible --version`.

## 🧹 Reset

Pour rejouer le challenge dans un état neutre :

```bash
make -C labs/decouvrir/installation-ansible/ clean
```

Cette cible désinstalle/supprime ce que la solution a posé sur les managed
nodes (paquets, fichiers, services, règles firewall) afin que vous puissiez
relancer la solution from scratch.

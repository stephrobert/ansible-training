# 🎯 Challenge — `requirements.yml` complet & pinné

## ✅ Objectif

Vérifier que `requirements.yml` (à la racine du lab) est conforme aux
attentes production :

| Attente | Cible |
| --- | --- |
| Section `roles:` présente | ≥ 1 rôle |
| Section `collections:` présente | ≥ 1 collection |
| **Tous** les rôles ont `version:` | Pinning obligatoire |
| ≥ 1 rôle depuis Git (`src:` contient `github.com`) | Source mixte |
| ≥ 1 rôle depuis Galaxy (sans `src:`) | Source mixte |
| ≥ 1 collection pinnée **strictement** (X.Y.Z exact) | Reproductibilité prod |

## 🧩 Indices

`requirements.yml` est déjà livré. Vérifiez-le et posez `solution.sh` :

```bash
echo "Lab 74 : requirements.yml validé par pytest." > challenge/solution.sh
chmod +x challenge/solution.sh
```

Si vous voulez tester l'installation réelle :

```bash
cd labs/galaxy/installer-roles/
ansible-galaxy role install -r requirements.yml -p /tmp/roles
ansible-galaxy collection install -r requirements.yml -p /tmp/collections
```

## 🚀 Lancement

Pas de playbook — c'est un lab manifeste. L'audit est purement statique.

## 🧪 Validation

```bash
pytest -v labs/galaxy/installer-roles/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/galaxy/installer-roles/ clean
```

## 💡 Pour aller plus loin

- **`signatures:`** sur les collections : vérification GPG cryptographique.
- **`include:`** : compose plusieurs `requirements.yml` modulaires.
- **`ANSIBLE_GALAXY_DISABLE_GPG_VERIFY=0`** : force la vérif GPG (RHCE 2026).

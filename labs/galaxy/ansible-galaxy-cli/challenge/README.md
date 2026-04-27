# 🎯 Challenge — Cheatsheet `ansible-galaxy` couvrant les 7 sous-commandes

## ✅ Objectif

Le test pytest valide que `cheatsheet.md` (à la racine du lab) couvre les
**7 sous-commandes essentielles** d'`ansible-galaxy` :

| Catégorie | Commandes attendues |
| --- | --- |
| Initialisation | `ansible-galaxy role init` |
| Installation | `ansible-galaxy role install`, `ansible-galaxy collection install` |
| Listing | `ansible-galaxy role list`, `ansible-galaxy collection list` |
| Build & Publish | `ansible-galaxy collection build`, `ansible-galaxy collection publish` |
| Vérification | `ansible-galaxy collection verify` |

Et le binaire `ansible-galaxy` doit répondre à `--version`.

## 🧩 Indices

C'est un challenge **documentaire** : `cheatsheet.md` est déjà livré. Vérifiez
qu'il couvre bien les 7 commandes ci-dessus, ajoutez ce qui manque (rare),
puis posez `solution.sh` minimal :

```bash
echo "Lab 73 : cheatsheet ansible-galaxy validé par pytest." > challenge/solution.sh
chmod +x challenge/solution.sh
```

## 🚀 Lancement

Pas de playbook à lancer — c'est un lab CLI local. Pour exécuter les commandes
de la cheatsheet manuellement :

```bash
ansible-galaxy --version
ansible-galaxy role list
ansible-galaxy collection list
```

## 🧪 Validation

```bash
pytest -v labs/galaxy/ansible-galaxy-cli/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/galaxy/ansible-galaxy-cli/ clean
```

## 💡 Pour aller plus loin

- **`ansible-galaxy collection install --upgrade`** : force l'upgrade.
- **`ansible-galaxy collection install --pre`** : autorise les versions
  préliminaires.
- **`~/.ansible/collections/`** : par défaut, où Ansible installe.
- **`ANSIBLE_COLLECTIONS_PATH`** : variable env pour customiser.

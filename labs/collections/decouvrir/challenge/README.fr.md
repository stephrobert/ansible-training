# 🎯 Challenge — Inventaire des collections installées

## ✅ Objectif

Déposer sur `db1.lab` un fichier `/tmp/lab93-collections.txt` qui contient l'inventaire des collections installées avec leurs **versions** et leur **path**, généré dynamiquement par Ansible.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab93-collections.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | Au moins 3 collections listées (`ansible.posix`, `community.general`, `kubernetes.core` ou autres présentes dans l'EE) |
| Format | Une collection par ligne, format `<FQCN_namespace.name> <version>` (ex: `community.general 10.5.0`) |
| Méthode | Utiliser `ansible.builtin.command` pour invoquer `ansible-galaxy collection list` puis `register:` + `copy` |

## 🧩 Bloqué ?

```bash
dsoxlab hint collections-decouvrir
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

Depuis la racine du repo :

```bash
ansible-playbook labs/collections/decouvrir/challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/collections/decouvrir/challenge/tests/
```

Le test pytest+testinfra valide :

- `/tmp/lab93-collections.txt` existe avec mode `0644`, owner `root`.
- Au moins 3 lignes non vides.
- Au moins une ligne contient un FQCN avec un point (ex: `community.general`).
- La solution est **idempotente** : un second passage n'annonce aucun changement (critère RHCE).

## 🧹 Reset

```bash
dsoxlab clean collections-decouvrir
```

## 💡 Pour aller plus loin

- **Lab 94** : `requirements.yml` pour reproduire l'environnement.
- **`ansible-galaxy collection list --format json`** : sortie scriptable pour intégration CI.
- **`ansible-lint --profile production`** : zéro warning attendu.

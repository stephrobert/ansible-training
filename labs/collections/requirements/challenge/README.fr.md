# 🎯 Challenge — `requirements.yml` multi-sources

## ✅ Objectif

Écrire un **`requirements.yml`** qui combine **3 sources** différentes, l'installer dans `local_collections/`, et déposer la liste des collections installées sur `db1.lab`.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab94-collections.txt` |
| Permissions | `0644`, owner `root` |
| Nombre de collections installées | **≥ 3** |
| Sources requises | Galaxy + Git + (URL **ou** dir) |
| Pinning | **Strict** (semver `version: "X.Y.Z"` ou tag Git) |

## 🧩 Bloqué ?

```bash
dsoxlab hint collections-requirements
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

```bash
ansible-playbook labs/collections/requirements/challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/collections/requirements/challenge/tests/
```

Le test pytest valide :

- `/tmp/lab94-collections.txt` existe avec mode `0644` et owner `root`.
- Au moins 3 collections listées dans le fichier.
- Au moins une collection avec un FQCN (point dans le namespace).

## 🧹 Reset

```bash
dsoxlab clean collections-requirements
```

## 💡 Pour aller plus loin

- **Signatures GPG** : ajouter `signatures:` à une collection + `--keyring` au lancement.
- **Renovate** : configurer un bot pour bumper auto `version: "X.Y.Z"` à chaque release upstream.
- **`ansible-lint --profile production`** : zéro warning attendu.

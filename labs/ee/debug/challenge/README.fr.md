# 🎯 Challenge : diagnostiquer puis corriger un EE cassé

## ✅ Mission

Le lab livre à sa racine une définition d'Execution Environment **cassée**
(`execution-environment-buggy.yml`, `requirements-buggy.yml`,
`requirements-buggy.txt`). Elle contient **4 défauts** qui empêchent
d'obtenir un EE utilisable. À vous de les trouver : tentez le build, lisez
les logs, vérifiez chaque dépendance, puis déposez une version corrigée
dans `challenge/`.

Livrables attendus (c'est ce que pytest vérifie) :

| Fichier à créer | Attente |
| --- | --- |
| `challenge/execution-environment.yml` | Schéma ansible-builder moderne complet, sections galaxy/python/system déclarées |
| `challenge/requirements.yml` | Uniquement des collections qui existent réellement sur Galaxy, en FQCN |
| `challenge/requirements.txt` | Uniquement des versions qui existent réellement sur PyPI |
| `challenge/bindep.txt` | Présent, dépendances système déclarées pour le profil rpm |

Les fichiers buggy de la racine ne doivent PAS être modifiés : ils servent
de pièce à conviction pour le diagnostic.

## 🧩 Bloqué ?

```bash
dsoxlab hint ee-debug
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 📓 Journal de commandes

Consignez dans `challenge/solution.sh` les commandes de diagnostic que vous
avez réellement passées (build, inspections podman, vérifications galaxy et
pip). Ce journal doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/ee/debug/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ee-debug
```

## 💡 Pour aller plus loin

- `ansible-builder create` : génère le Containerfile sans builder l'image,
  idéal pour un diagnostic rapide.
- `podman run -it --entrypoint /bin/bash <ee>` : shell interactif dans
  l'image pour inspection.
- `ansible-navigator collections --eei <ee>` : lister les collections
  réellement embarquées.

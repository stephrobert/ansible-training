# Le build annonce un succès et l'image ne sait pas lancer Ansible

## La situation

Un collègue vous laisse une recette d'EE et un problème. Le build n'affiche
aucune erreur qui mérite qu'on s'arrête, l'image arrive sur le registre, et le
premier playbook qui tente de l'utiliser meurt aussitôt : il n'y a pas de commande
`ansible` dedans. Plusieurs fautes se cachent dans ces fichiers, et la plus
vicieuse est celle qui n'échoue pas. Le build ne vous ment pas : vous ne lisez pas
la bonne ligne de sa sortie.

Votre mission, depuis le répertoire du projet :

1. Tenter le build de la **recette cassée** telle quelle, verbosité poussée, et
   inspecter l'image obtenue plutôt que de croire son code de retour.
2. Expliquer pourquoi l'image est livrée **sans `ansible-core`** alors que la
   recette le réclame noir sur blanc, et retrouver l'avertissement qui l'annonçait.
3. Débusquer les deux dépendances qui n'existent pas, une collection et une version
   Python, et prouver que chacune manque à la source plutôt que d'accuser le réseau
   ou un proxy.
4. Produire un **jeu de fichiers corrigé**, complété par les dépendances système
   que l'original avait oubliées, le builder, et prouver que l'image contient
   enfin ce qu'elle prétend.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/debug-ee-casse/

## 🎯 Challenge : diagnostiquer puis corriger un EE cassé

### ✅ Mission

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

### 🧩 Bloqué ?

```bash
dsoxlab hint ee-debug
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 📓 Journal de commandes

Consignez dans `challenge/solution.sh` les commandes de diagnostic que vous
avez réellement passées (build, inspections podman, vérifications galaxy et
pip). Ce journal doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/ee/debug/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ee-debug
```

### 💡 Pour aller plus loin

- `ansible-builder create` : génère le Containerfile sans builder l'image,
  idéal pour un diagnostic rapide.
- `podman run -it --entrypoint /bin/bash <ee>` : shell interactif dans
  l'image pour inspection.
- `ansible-navigator collections --eei <ee>` : lister les collections
  réellement embarquées.

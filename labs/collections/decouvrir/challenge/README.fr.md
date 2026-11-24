# « module introuvable », alors que le module est là

## La situation

Un playbook qui tourne depuis deux ans échoue sur le nouveau nœud de contrôle :
module introuvable. Le module existe, il est simplement appelé par son nom court,
et la collection qui le fournit n'est pas installée ici. Personne ne sait dire
quelles collections cet environnement embarque réellement, ni d'où elles viennent.
Pendant ce temps, le linter s'est mis à rejeter les noms courts, et « ça marchait
avant » va cesser d'être un argument sur toute la base de code.

Votre mission, depuis **control-node.lab** :

1. Inventorier les collections réellement installées dans l'environnement, avec
   leurs **versions** et leur emplacement sur le disque, et faire écrire cet
   inventaire par le play dans un fichier sur **db1.lab**, pas dans votre terminal.
2. Lire les métadonnées propres à une collection pour savoir qui la publie, quelle
   version elle revendique et de quoi elle dépend.
3. Parcourir sa structure et dire ce qu'une collection peut transporter au-delà des
   modules : plugins, rôles, playbooks, documentation.
4. Prendre un module que vous appelez tous les jours, retrouver la collection dont
   il vient, et écrire son **nom pleinement qualifié**. C'est ce que le linter
   exigera demain.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/

## 🎯 Challenge — Inventaire des collections installées

### ✅ Objectif

Déposer sur `db1.lab` un fichier `/tmp/lab93-collections.txt` qui contient l'inventaire des collections installées avec leurs **versions** et leur **path**, généré dynamiquement par Ansible.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab93-collections.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | Au moins 3 collections listées (`ansible.posix`, `community.general`, `kubernetes.core` ou autres présentes dans l'EE) |
| Format | Une collection par ligne, format `<FQCN_namespace.name> <version>` (ex: `community.general 10.5.0`) |
| Méthode | Utiliser `ansible.builtin.command` pour invoquer `ansible-galaxy collection list` puis `register:` + `copy` |

### 🧩 Bloqué ?

```bash
dsoxlab hint collections-decouvrir
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

Depuis la racine du repo :

```bash
ansible-playbook labs/collections/decouvrir/challenge/solution.yml
```

### 🧪 Validation automatisée

```bash
pytest -v labs/collections/decouvrir/challenge/tests/
```

Le test pytest+testinfra valide :

- `/tmp/lab93-collections.txt` existe avec mode `0644`, owner `root`.
- Au moins 3 lignes non vides.
- Au moins une ligne contient un FQCN avec un point (ex: `community.general`).
- La solution est **idempotente** : un second passage n'annonce aucun changement (critère RHCE).

### 🧹 Reset

```bash
dsoxlab clean collections-decouvrir
```

### 💡 Pour aller plus loin

- **Lab 94** : `requirements.yml` pour reproduire l'environnement.
- **`ansible-galaxy collection list --format json`** : sortie scriptable pour intégration CI.
- **`ansible-lint --profile production`** : zéro warning attendu.

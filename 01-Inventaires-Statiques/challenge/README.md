# 🎯 Challenge - Inventaire Statique avec Groupe et Variables

Dans ce challenge, vous allez renforcer votre maîtrise des **inventaires
statiques au format INI** en ajoutant un **nouveau groupe** avec des **variables
spécifiques**.

## ✅ Objectif

* Ajouter un groupe `[dbservers]` à l'inventaire `fichiers/hosts.ini`
* Ajouter **au moins deux hôtes** dans ce groupe
* Définir deux variables pour ce groupe :

  * `db_port=5432`
  * `db_engine=postgresql`

## 🧩 Consignes

1. Editez le fichier `fichiers/hosts.ini`
2. Ajoutez à la fin du fichier le groupe et le variables.
3. Exécutez la commande suivante pour vérifier que le groupe est bien présent :

```bash
ansible-inventory -i fichiers/hosts.ini --list -y
```

4. Vérifiez que les deux hôtes `db1.local` et `db2.local` sont bien affectés au
   groupe `dbservers`, et que les variables `db_port` et `db_engine`
   apparaissent bien dans la sortie.

## 🧪 Validation

Le script `test_inventory.py` vérifiera automatiquement :

* La présence du groupe `dbservers`
* La présence d'au moins deux hôtes dans ce groupe
* La présence des variables `db_port` et `db_engine` dans la définition du
  groupe

Pour lancer les tests, utilisez la commande :

```bash
pytest -v challenge/tests/test_inventory.py
```

## 🚀 Pour aller plus loin

Vous pouvez ensuite ajouter un fichier `group_vars/dbservers.yml` pour tester
l'autre méthode de définition de variables de groupe.

---

Bonne chance et bon inventaire ! 🧠

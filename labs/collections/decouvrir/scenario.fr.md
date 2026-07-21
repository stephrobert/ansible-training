# Contexte : « module introuvable », alors que le module est là

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
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/

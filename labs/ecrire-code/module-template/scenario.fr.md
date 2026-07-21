# Contexte : on écrase la config, on perd la preuve

La bannière de **db1.lab** est générée depuis un template, désormais, et c'est
un progrès. Ce qui n'en est pas un : le run de la semaine dernière l'a
remplacée par une version cassée, et personne n'a pu produire la précédente.
Elle existait à exactement un endroit : le fichier qui venait d'être écrasé.
Sur une bannière, ça coûte des excuses. Sur la configuration d'un service qui
refuse de redémarrer, un vendredi à 18 heures, ça coûte la soirée. Vous
sécurisez la génération depuis **control-node.lab**.

Votre mission :

1. Générer `/etc/banner.txt` sur `db1.lab` depuis un **template Jinja2**, le
   texte d'en-tête venant d'une variable plutôt que d'une chaîne en dur.
2. Construire le bloc de métadonnées en **itérant sur un dict**, pour
   qu'ajouter un champ plus tard revienne à modifier la donnée, pas le
   template.
3. Conserver la version précédente : chaque écrasement doit laisser derrière
   lui une **sauvegarde horodatée**.
4. Poser les permissions explicitement et **quoter le mode** : un octal non
   quoté n'est pas le mode que vous croyez. Puis découvrir ce que `validate:`
   vous apporterait sur une vraie config.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/module-template/

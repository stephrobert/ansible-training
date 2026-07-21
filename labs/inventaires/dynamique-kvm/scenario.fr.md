# Contexte : cesser d'entretenir un inventaire que l'hyperviseur connaît déjà

L'inventaire statique ment. Deux VMs qu'il liste ont été détruites le mois
dernier, une troisième a été renommée, et chaque exécution perd du temps en
timeouts sur des hôtes qui n'existent plus. Pendant ce temps, libvirt sait
exactement ce qui tourne sur l'hyperviseur. Pire, le fichier mélange les VMs
éteintes et les vivantes : un play visant « tout » échoue toujours sur celles
qui sont arrêtées. Vous branchez l'inventaire sur la source de vérité depuis
**control-node.lab**.

Votre mission :

1. Faire **découvrir les VMs automatiquement** par libvirt via le plugin
   d'inventaire, en gardant à l'esprit que l'inventaire devient un
   **répertoire** que le plugin compose, et non un fichier écrit à la main.
2. Utiliser les **groupes d'état dynamiques** générés par le plugin, qu'aucun
   fichier statique ne déclare, pour isoler les VMs en cours d'exécution.
3. Viser l'**intersection** du groupe statique du lab et des VMs running : une
   VM éteinte ne doit pas être tentée, et une VM running hors du lab ne doit pas
   être touchée.
4. Poser un marqueur sur chaque VM réellement atteinte, prouvant que la
   découverte reflète l'état **au moment de l'exécution**.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/dynamiques/plugin-libvirt-kvm/

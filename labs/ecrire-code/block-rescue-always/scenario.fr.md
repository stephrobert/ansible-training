# Contexte : la migration est morte en chemin et a laissé la porte ouverte

Une migration sur **db1.lab** a échoué en plein milieu le mois dernier. Elle
avait déjà basculé le service en mode maintenance, et elle ne l'en a jamais
sorti : l'échec a interrompu le playbook sur place, et l'étape de nettoyage,
bien rangée en bas du fichier, n'a jamais tourné. L'hôte est resté hors
rotation jusqu'à ce que quelqu'un s'en aperçoive. L'erreur n'est pas le
problème : une erreur sans rattrapage ni nettoyage, si. Vous reconstruisez le
play depuis **control-node.lab**, avec une vraie transaction autour.

Votre mission :

1. Regrouper les tâches risquées dans un **`block:`** sur `db1.lab`, dont une
   qui échouera à coup sûr.
2. Capturer cet échec dans un **`rescue:`** qui consigne ce qui s'est passé, au
   lieu de laisser le play mourir sur place.
3. Garantir que le nettoyage tourne dans **`always:`**, que le block ait réussi
   ou explosé.
4. Lire le récapitulatif : **`failed=0`**. L'erreur a eu lieu, elle a été
   traitée, le play est un succès. Puis trouver la variable qui dit au `rescue`
   ce qui a réellement échoué.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/block-rescue-always/

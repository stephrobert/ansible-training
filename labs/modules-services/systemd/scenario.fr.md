# Contexte : corriger la dérive d'horloge et prouver un démarrage propre

Corréler les logs du parc a viré au jeu de devinettes la semaine dernière :
**web1.lab** dérive de plusieurs secondes, si bien que ses horodatages ne
s'alignent plus avec ceux des autres serveurs pendant un incident. La
synchronisation de temps doit tourner et surtout **revenir toute seule après un
reboot**, ce que le `systemctl start` manuel n'a jamais garanti. L'équipe ops
veut aussi un marqueur de boot : une petite unit qui pose un drapeau au
démarrage, pour reconnaître d'un coup d'œil un hôte remonté proprement.

Votre mission :

1. Depuis **control-node.lab**, installer le service de synchronisation de temps
   sur **web1.lab**, puis le rendre **démarré maintenant et activé au boot** :
   ce ne sont pas la même chose.
2. Déposer un **unit file custom** `lab-marker.service` qui pose son drapeau une
   fois au démarrage et reste ensuite marqué actif.
3. Faire en sorte que systemd **prenne réellement en compte la nouvelle unit**
   avant de l'activer et de la démarrer, sans quoi elle reste invisible derrière
   le cache.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-systemd/

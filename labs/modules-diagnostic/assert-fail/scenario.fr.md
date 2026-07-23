# Contexte : arrêter le playbook avant qu'il n'abîme la mauvaise machine

Le retour d'incident a été sans détour. Un playbook écrit pour la famille RHEL a
tourné sur un hôte qui n'en était pas, a échoué à mi-parcours, et a laissé le
système dans un état que personne ne savait décrire : à moitié configuré, à
moitié intact. Il ne vérifiait rien avant de démarrer. Celui-ci ne refera pas la
même erreur. Il est prévu pour **db1.lab**, pour une distribution récente de la
famille RHEL, sur une machine dotée d'assez de mémoire, et il doit **refuser de
s'exécuter** ailleurs plutôt que d'échouer en cours de route.

Votre mission :

1. Depuis **control-node.lab**, faire **refuser au play tout hôte autre que
   db1.lab**, avec un message qui dit pourquoi, vérifié **avant** toute autre
   exécution.
2. **Valider les prérequis** d'un seul bloc : une distribution de la famille
   RHEL, une version majeure supérieure ou égale à 9, et au moins 512 Mo de RAM.
3. Rendre l'échec **lisible** : un message personnalisé en cas d'échec, un autre
   en cas de succès, pour que le log raconte ce qui s'est passé au lieu de
   cracher un booléen brut.
4. Ne poser qu'**après** validation le marqueur qui prouve que l'hôte a passé le
   filtre.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-assert-fail/

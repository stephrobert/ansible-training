# Contexte : le hub n'accepte plus votre rôle, et vos utilisateurs l'ignorent

Votre rôle standalone est publié, utilisé par des équipes que vous n'avez jamais
rencontrées, et la plateforme sur laquelle vous publiez ne prend plus que des
collections. Le rôle doit donc déménager. La contrainte : personne en aval ne
modifiera ses playbooks à votre calendrier. Ces gens appellent votre module par son
ancien nom, dans du code qui ne vous appartient pas, et un renommage qui les casse
est votre problème, pas le leur. Il faut que la migration soit invisible aujourd'hui
et assez visible pour qu'ils bougent un jour.

Votre mission, depuis **control-node.lab** :

1. Déplacer le rôle **et son module custom** dans une collection sous votre
   namespace, en plaçant chacun là où la structure d'une collection l'attend.
2. Mettre en place une **redirection** pour qu'un playbook appelant le module par
   son **ancien nom** continue de fonctionner, résolu vers le nouvel emplacement
   sans que personne n'édite quoi que ce soit.
3. Prouver que les **deux** noms marchent contre **db1.lab** : le nouveau nom
   pleinement qualifié, et l'ancien qui passe par la redirection.
4. Vérifier que le chemin hérité émet un **avertissement de dépréciation**. Une
   compatibilité silencieuse est une compatibilité éternelle, et ce n'est pas le
   contrat.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/migration-role/

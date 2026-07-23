# Contexte : la suite de tests qui passe sur un mensonge

Votre scénario Molecule est vert, et il ne prouve presque rien. L'instance
démarre nue : le rôle installe lui-même ses prérequis et le test n'éprouve jamais
l'état de départ réel. Le run ne tire aucune collection : il passe en local et
explose en CI. Personne ne sait quelle tâche mange les quatre minutes. Et le
cycle ne rejoue jamais le rôle : un rôle qui modifie quelque chose à chaque
passage se déclare quand même en succès. Une suite verte incapable d'échouer
n'est qu'une décoration.

Votre mission, depuis le répertoire du projet :

1. Préconditionner l'instance avant l'application du rôle, pour que le test
   parte de l'état d'un vrai serveur, et déclarer les dépendances Galaxy du
   scénario au lieu de compter sur ce qui traîne déjà installé.
2. Donner à chaque instance ses propres variables, pour que le scénario cesse de
   supposer que toutes les plateformes se ressemblent.
3. Figer explicitement l'ordre des étapes du cycle, et y inclure l'étape
   d'**idempotence** : la suite doit pouvoir attraper un rôle qui ne se
   stabilise jamais.
4. Activer le chronométrage des tâches, et désigner la plus lente.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/molecule-installation-config/

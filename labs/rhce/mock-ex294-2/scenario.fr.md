# Contexte : quatre heures, sans moteur de recherche, sur une machine inconnue

C'est le second examen blanc. Même épreuve, autre décor : une pile Apache et
valkey là où le premier mock faisait tourner nginx et mariadb, d'autres
utilisateurs, un autre découpage disque, d'autres ports et un autre horaire.
Tout ce qu'un candidat aurait pu retenir par cœur de sa première tentative ne
vaut plus rien ici, et c'est le but. Ce qui survit au changement de décor, c'est
la compétence.

Dix-neuf tâches indépendantes réparties sur les quatre machines du lab, quatre
heures, et pour toute documentation ce qui est livré avec Ansible. Une tâche
compte quand elle s'exécute proprement et que son résultat tient à l'inspection.

Votre mission, depuis **control-node.lab** :

1. Lancer le chrono et traiter les dix-neuf tâches : inventaires et variables,
   fichiers, paquets, services, utilisateurs, stockage, sécurité, rôles et vault,
   puis gestion d'erreur, déploiement par vagues, délégation, tags, tâches
   planifiées, facts personnalisés et une content collection installée depuis un
   `requirements.yml`, sur **web1.lab**, **web2.lab** et **db1.lab**.
2. **Vérifier chaque tâche dès qu'elle est finie.** Les candidats qui gardent la
   vérification pour la fin découvrent leurs erreurs à quarante minutes du terme,
   sans le temps de les corriger.
3. Gérer le temps comme à un examen, pas comme à un lab : une tâche qui résiste,
   on l'abandonne et on y revient.
4. Faire un débriefing honnête à la fin. Ce que vous avez dû chercher est votre
   vraie faiblesse, et c'est le seul produit utile d'un examen blanc. Sous trois
   heures : vous êtes prêt.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/certifications/rhce/

# Contexte : la faute de frappe qui n'a explosé qu'au bout de dix minutes

Hier, un collègue a appelé votre rôle `webserver` avec `webserver_state:
enabled`. Ce choix n'existe pas. Ansible n'a rien dit, a tourné dix minutes, puis
est mort au fond d'une tâche de paquet dans une trace illisible. La valeur était
fausse dès la première seconde, mais le rôle n'avait aucun moyen de le signaler.
Un rôle qui fait confiance à ses entrées fait payer son silence à ses
utilisateurs.

Votre mission, depuis **control-node.lab** :

1. Déployer le rôle `webserver` sur **db1.lab** avec des entrées **valides** :
   port d'écoute **8090**, un état de paquet et un état de service pris parmi les
   valeurs autorisées, et une page d'accueil personnalisée.
2. Faire en sorte que le rôle **type, contraigne et documente** ses variables
   d'entrée, pour qu'une valeur fausse soit rejetée **avant la première tâche**.
3. Lui passer volontairement une valeur invalide et lire le message de rejet :
   il doit nommer la variable et énumérer ce qui était permis.
4. Vérifier qu'un run aux valeurs valides franchit la validation sans accroc.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/argument-specs/

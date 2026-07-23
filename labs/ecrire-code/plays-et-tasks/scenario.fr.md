# Contexte : « le redémarrage est passé après le feu vert »

Le dernier déploiement sur **db1.lab** a laissé l'équipe perplexe : le bandeau
de maintenance est apparu avant même que le service soit installé, et le
redémarrage a eu lieu après l'envoi de la notification de fin. Personne n'a
ouvert de bug. Le playbook était une seule longue liste `tasks:` à plat : tout
s'est exécuté dans l'ordre d'écriture, et rien dans le bon ordre. Un play a
des sections, et elles existent précisément pour ça.

Vous le réécrivez proprement depuis **control-node.lab**.

Votre mission :

1. Structurer un play sur `db1.lab` autour de **`pre_tasks`**, **`tasks`**,
   **`post_tasks`** et **`handlers`**.
2. Déployer `nginx`, démarré et activé, servant une page qui identifie l'hôte
   par son nom d'inventaire.
3. Faire en sorte que la modification de config **notifie** un handler de
   redémarrage, au lieu de redémarrer à chaque passage.
4. Prouver l'ordre d'exécution réel avec des **fichiers marqueurs horodatés** :
   le marqueur predeploy doit être antérieur au marqueur postdeploy.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/plays-et-tasks/

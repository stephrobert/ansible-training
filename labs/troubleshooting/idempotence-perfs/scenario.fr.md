# Contexte : du jaune à chaque run, et plus personne ne lit le recap

Le play nocturne annonce `changed=14` toutes les nuits, sur des hôtes où rien n'a
bougé depuis des semaines. Les tâches mentent sur leur état : elles refont le
travail, elles invalident des caches, et elles ont appris à l'équipe à ignorer le
recap. C'est précisément pour cela que le vrai changement de mardi dernier est
passé inaperçu pendant trois jours. Par-dessus le marché, le play met onze minutes,
et la direction commence à demander pourquoi.

Votre mission, depuis **control-node.lab** :

1. Refondre les trois opérations fautives sur **db1.lab** pour que le play affiche
   **`changed=0` au second passage** : une commande brute qui ne doit pas se
   rejouer, une ligne de configuration qui doit être reconnue plutôt qu'ajoutée, et
   une lecture seule qui n'a rien à faire dans les changements.
2. Prouver la correction de la seule façon qui compte : lancer deux fois et lire le
   recap.
3. Mesurer un **point de référence** avant d'optimiser : nommer les tâches qui
   coûtent réellement les onze minutes, plutôt qu'optimiser par tradition orale.
4. Régler ensuite la couche de connexion : moins d'allers-retours par tâche, plus
   d'hôtes en parallèle, une connexion SSH réutilisée. Remesurer et annoncer le
   gain réel.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/idempotence-cassee/

# Contexte : le code d'un inconnu, en root, sur votre production

Un développeur veut faire entrer un rôle Galaxy dans le projet avant vendredi. Il
a beaucoup d'étoiles, donc la discussion est considérée comme close. Elle ne
l'est pas. Ce rôle est du code arbitraire qui s'exécutera avec **`become: true`**
sur tous vos serveurs de production, et personne dans la pièce ne l'a ouvert. Les
étoiles mesurent la popularité, pas le fait que la chose télécharge un binaire en
HTTP clair ou qu'elle soit abandonnée depuis 2021.

Votre mission, depuis le répertoire du projet :

1. Transformer le vague sentiment que « ça a l'air correct » en une **grille
   notée** sur six axes : santé du mainteneur, qualité du code, sécurité, tests,
   compatibilité, idempotence.
2. Lire la carte d'identité déclarée par le rôle pour savoir quelles plateformes
   il prétend réellement supporter, et la confronter à votre parc.
3. Traquer les signaux classiques : secrets en dur, téléchargements non chiffrés,
   noms de modules courts, commandes arbitraires sans rien pour les rendre
   idempotentes.
4. Convertir la note en une **décision** défendable : adopter, forker ou refuser.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/auditer-role-existant/

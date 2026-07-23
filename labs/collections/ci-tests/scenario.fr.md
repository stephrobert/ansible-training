# Contexte : votre collection embarque du Python, et c'est là qu'elle cassera

Un rôle, c'est du YAML, et le YAML survit assez bien à une montée de version.
Votre collection, elle, embarque un module Python, et il casse sur des choses
qu'un rôle ne remarque jamais : une version de Python qui a retiré un appel de la
bibliothèque standard, un `ansible-core` qui a changé un import de module_utils.
Les utilisateurs le rencontrent, vous non, parce que votre poste ne tourne que sur
une seule combinaison. Et le workflow censé l'attraper utilise des tags flottants
et un token qui a plus de droits que nécessaire.

Votre mission, depuis le répertoire du projet :

1. Croiser les **versions d'`ansible-core` et de Python** dans une matrice, au
   moins deux de chaque, pour tester les combinaisons que vos utilisateurs vivent.
2. Lancer les **tests de sanity et les tests unitaires** de la collection en
   conteneur, pour que le verdict ne dépende pas de ce qui traîne sur le runner.
3. Durcir le workflow lui-même : **aucune permission globale**, chaque job ne
   recevant que son strict nécessaire, et **aucun identifiant laissé** derrière le
   checkout.
4. **Épingler chaque action tierce par SHA de commit** : un tag peut être déplacé
   sous vos pieds, et un linter supply-chain vous le dira.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/pipeline-ci/

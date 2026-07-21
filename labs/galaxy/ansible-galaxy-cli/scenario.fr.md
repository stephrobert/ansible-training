# Contexte : toute l'équipe cherche la même commande chaque semaine

`ansible-galaxy` fait sept métiers différents et personne dans l'équipe n'en
retient plus de trois. L'un réinvente à la main un squelette de rôle en ayant
oublié qu'`init` existe. L'autre installe une collection dans le mauvais chemin.
Un troisième tente de publier et découvre, au pire moment, qu'il faut d'abord
builder un tarball. Deux nouveaux arrivent lundi, et la réponse d'onboarding ne
peut plus être « demande sur le chat ».

Votre mission, depuis le répertoire du projet :

1. Produire la référence de l'équipe pour la CLI : **générer** un rôle et une
   collection, **installer** depuis Galaxy et depuis Git, **lister** ce qui est
   réellement présent en local.
2. Couvrir le chemin de publication de bout en bout : **builder** le tarball, le
   **publier** avec un token API, et **vérifier** l'intégrité de ce qui redescend.
3. Pour chaque commande, préciser où elle écrit : c'est là qu'est le piège, rôles
   et collections n'atterrissent pas au même endroit.
4. Confronter votre référence au binaire réel plutôt qu'à vos souvenirs.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ansible-galaxy-cli/

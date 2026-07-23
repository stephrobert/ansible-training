# Contexte : un playbook que personne ne peut annuler

Votre équipe range ses playbooks dans un dossier partagé. La semaine dernière,
quelqu'un a écrasé `site.yml`, le changement a cassé la production, et impossible
de savoir à quoi ressemblait le fichier avant. Pas d'historique, pas de blame,
pas de retour arrière. La solution n'est pas une plateforme sophistiquée : c'est
Git, utilisé comme l'attend l'objectif EX294 « Manage content in a git
repository », ni plus ni moins.

Tout se passe sur **votre propre poste de contrôle**. Aucun managed node, aucune
forge distante : un dépôt **bare** local tient lieu de serveur, ce qui vous fait
pratiquer le `push` sans réseau.

Votre mission :

1. **Initialiser** un dépôt Git pour un petit projet de playbooks, sur la
   branche `main`.
2. Poser une **identité d'auteur locale** sur ce dépôt.
3. **Suivre et committer** les playbooks, puis ajouter un second playbook dans
   son propre commit pour que le dépôt ait un vrai **historique**.
4. **Pousser** l'historique vers un dépôt bare local et confirmer qu'il est bien
   arrivé (même commit des deux côtés).

Restez au niveau de l'objectif : pas de CI, pas de GitOps, pas de forge
distante. Juste init, add, commit, push, faits correctement.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/pratiques/versionner-git/

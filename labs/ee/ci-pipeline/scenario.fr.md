# Contexte : votre EE a été construit à la main, et il a neuf mois

L'EE sur mesure fait tourner toute la production, et il a été construit sur un
portable l'automne dernier. Depuis, son image de base a accumulé des CVE
critiques, personne ne l'a reconstruit parce que personne n'en est propriétaire,
et personne ne peut prouver que l'image du registre est bien celle qui a été
construite : elle a été poussée depuis un poste avec un token personnel. Un
artefact qui fait tourner tout un parc ne peut pas sortir de l'après-midi de
quelqu'un.

Votre mission, depuis le répertoire du projet :

1. Construire l'EE en **CI** plutôt que sur un poste, pour qu'un rebuild soit à un
   commit de distance et que l'horloge des CVE cesse de tourner sans surveillance.
2. **Scanner l'image et bloquer dessus** : un build qui trouve des vulnérabilités
   hautes ou critiques doit faire échouer le pipeline, pas prévenir dans un log
   que personne ne lit.
3. **Signer l'image** en keyless, pour que les consommateurs vérifient que
   l'artefact vient de votre pipeline et non d'un poste, puis la publier.
4. Durcir le pipeline lui-même : **épingler les actions tierces par SHA de
   commit**, garder des permissions globales vides et n'accorder à chaque job que
   son strict nécessaire, sans laisser d'identifiants derrière le checkout.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/exec-playbook/#pipeline-github-actions

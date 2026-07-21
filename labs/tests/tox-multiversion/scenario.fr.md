# Contexte : un bug remonté depuis une version que vous n'avez jamais lancée

Une issue tombe sur votre rôle publié : il échoue sur `ansible-core` 2.16. Vous
n'arrivez pas à reproduire, parce que votre poste tourne en 2.18 et n'a jamais
fait autrement. Vos utilisateurs, eux, sont ailleurs : certains sont figés sur
la LTS par leur équipe plateforme, d'autres sont déjà sur la dernière version, et
votre suite mono-version est aveugle aux deux. Reproduire à la main impose de
reconstruire un virtualenv par version, et personne dans l'équipe ne le fera deux
fois.

Votre mission, depuis le répertoire du projet :

1. Déclarer un environnement **par version d'`ansible-core`** à supporter, chacun
   isolé et épinglant la sienne, pour qu'aucune version ne déborde sur l'autre.
2. Faire lancer à chaque environnement le cycle Molecule complet sur le même
   rôle, pour que « ça passe » veuille dire la même chose partout.
3. Rendre toute la matrice jouable en **une seule commande**, et une version
   précise ciblable à la demande quand vous traquez un échec particulier.
4. Lire le verdict : une divergence entre environnements est un bug de
   portabilité du rôle, pas un test instable.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/tests-tox-multiversion/

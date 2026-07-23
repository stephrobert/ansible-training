# Contexte : la revue qui rejoue toujours la même dispute

Chaque merge request sur les rôles de l'équipe rouvre le même débat : noms de
modules courts, tâches sans `name:`, un `shell:` là où un module dédié existe,
`yes` au lieu de `true`. Les relecteurs en ont assez de servir de linter. Et le
mois dernier, quelqu'un a commité une clé privée : elle est restée trois jours
dans l'historique avant que personne ne le remarque. Le style se négocie en
revue ; une clé qui fuit, non. Les deux relèvent d'une machine, et cette machine
doit dire non avant que le commit existe.

Votre mission, depuis le répertoire du projet :

1. Épingler le linter sur son **profil le plus strict**, celui qu'on exige d'un
   code livré en production, et écouter ce qu'il dit du rôle tel qu'il est.
2. Ajouter par-dessus une politique YAML stricte : les booléens ambigus et le
   formatage approximatif cessent de passer en revue parce qu'ils cessent de
   passer l'outil.
3. Câbler les deux dans un **hook Git** joué à chaque commit, pour qu'aucun code
   non conforme n'atteigne la branche et que la CI ne fasse que confirmer.
4. Ajouter un hook qui **bloque les fuites de secrets** dès le commit, clés
   privées comprises.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ansible-lint-production-profile/

# Contexte : vous avez renommé une variable et cassé quatre équipes

Votre rôle `webserver` est utilisé dans toute l'entreprise. À la dernière
release, vous avez renommé une variable d'entrée, livré ça en correctif, et quatre
projets ont cassé au run suivant. Ils n'avaient rien fait de mal : ils épinglaient
une plage de patch, parce qu'un patch est censé être sans risque. La casse était
réelle, mais le mensonge était dans le numéro de version. Un consommateur ne peut
pas épingler sainement si la numérotation du publieur ne veut rien dire.

Votre mission, depuis le répertoire du projet :

1. Poser la règle : **quel chiffre bouge** et quand. Ce qui impose une majeure, ce
   qui mérite une mineure, ce qui est vraiment un correctif, et où tombe un
   renommage.
2. Tenir un **changelog** exploitable, classé par version et par nature de
   changement, pour qu'un lecteur sache en dix secondes si la montée fait mal.
3. Poser la release en **tag Git annoté**, et documenter la procédure pour
   qu'elle soit reproductible par quelqu'un d'autre que vous.
4. Automatiser la publication depuis la CI sur ce tag, et documenter comment le
   **consommateur** doit épingler le résultat.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/versionner-publier/

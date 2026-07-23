# Contexte : « montrez-moi ce que ça va changer, avant que ça change »

Le comité de validation des changements pose toujours la même question avant
un run sur **db1.lab**, et elle est légitime : qu'est-ce que ce playbook va
toucher, exactement ? Le trimestre dernier, un playbook a réécrit un fichier
sous `/etc` que personne n'attendait, et le « ça devrait bien se passer » n'a
pas survécu au post-mortem. Nouvelle règle : tout changement est répété à
blanc, son diff est lu à voix haute, et seulement ensuite le même playbook
tourne pour de vrai. Vous répétez ce workflow depuis **control-node.lab** sur
un fichier marqueur inoffensif.

Votre mission :

1. Écrire un play qui dépose `/etc/lab-checkmode.txt` sur `db1.lab`, en mode
   `0644`, avec un contenu connu.
2. Le lancer d'abord en **`--check --diff`** : lire le bloc avant/après, puis
   confirmer sur `db1.lab` que rien n'a réellement été écrit.
3. Le lancer pour de vrai et vérifier que le diff correspond exactement à ce
   qu'annonçait le run à blanc.
4. Le lancer une troisième fois : aucun diff, `changed=0`. Puis identifier les
   modules incapables de simuler, et savoir forcer une tâche en lecture seule
   à s'exécuter malgré le check mode.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/checkmode-diff/

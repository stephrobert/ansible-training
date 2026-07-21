# Contexte : un identifiant que personne ne devrait avoir à taper

L'outil de support corrèle les incidents par un identifiant système : nom
court de l'hôte, puis noyau en cours d'exécution. Aujourd'hui, quelqu'un
compose cette chaîne à la main et la colle dans le ticket, en se trompant à
peu près une fois sur cinq, en général juste après une mise à jour de noyau,
quand la machine ne fait plus tourner ce que le ticket prétend. L'hôte connaît
parfaitement les deux moitiés. Il suffit de les lui demander, d'assembler la
réponse, et de l'écrire. Vous le faites sur **db1.lab** depuis
**control-node.lab**, sans collecter tous les facts.

Votre mission :

1. Capturer le **nom court de l'hôte** et la **version du noyau** avec deux
   commandes en lecture seule, en conservant chaque résultat.
2. Garantir que ces lectures ne se déclarent jamais `changed` : une commande
   qui se contente de regarder le système ne change rien et doit le dire, sinon
   votre playbook n'est plus jamais idempotent.
3. Assembler les deux valeurs capturées en un seul **fact de runtime**.
4. L'écrire sur db1 sous la forme `system_id=<hostname>:<kernel>`, et savoir où
   se situe un `set_fact` dans l'ordre de précédence, et ce que change
   `cacheable`.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/register-set-fact/

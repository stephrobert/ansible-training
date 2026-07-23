# Contexte : quatre-vingt-dix tâches à rejouer pour corriger un mot

Le play de déploiement meurt à la tâche 91 sur **db1.lab** : une variable non
définie, et aucun moyen de savoir ce qu'elle aurait dû valoir. Alors vous devinez,
vous éditez le YAML, et vous relancez tout depuis le début. Quatre-vingt-dix
tâches, douze minutes, mauvaise pioche. Deuxième tentative : quatre-vingt-dix
tâches, douze minutes. Chaque itération d'une correction d'un mot coûte une pause
café, et le run ne vous laisse jamais regarder autour de vous à l'instant précis
où il sait quelque chose.

Votre mission, depuis **control-node.lab** :

1. Armer le play pour qu'une tâche en échec **ouvre une session au lieu de tuer le
   run**, à l'endroit exact où l'état est encore disponible.
2. Depuis là, inspecter ce que le run sait : la tâche telle qu'elle a été résolue,
   les variables dans la portée, et le résultat du module lui-même.
3. Corriger la panne **à chaud**, en fournissant la valeur manquante dans la
   session vivante plutôt que dans le fichier, et **rejouer cette seule tâche**
   pour valider votre hypothèse.
4. Une fois le run terminé, inscrire proprement la correction dans le playbook,
   pour que la valeur ne dépende plus de quelqu'un devant son clavier.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/debugger-interactif/

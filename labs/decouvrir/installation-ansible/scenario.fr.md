# Contexte : « chez moi ça marche »

Un collègue vous passe un playbook qui tourne très bien sur son portable et
meurt sur le vôtre avec un laconique « couldn't resolve module/action ». Deux
heures plus tard, le coupable apparaît : une collection manquante. Personne
n'avait jamais écrit ce qu'un poste doit réellement embarquer pour mériter le
nom de control node, alors chacun le redécouvre à ses dépens. Vous allez coder
cette vérification une fois pour toutes.

Tout se passe sur **votre propre control node**, aucun managed node impliqué.

Votre mission :

1. Identifier comment Ansible a été installé ici, et refuser toute version
   antérieure à **ansible-core 2.18**.
2. Vérifier la présence des **8 binaires standard** dans le `PATH` : un control
   node sans `ansible-vault` ne sait pas gérer le moindre secret.
3. Vérifier qu'une vraie bibliothèque de modules est accessible (**au moins
   100 modules** via `ansible-doc`) et que les **3 collections** utilisées par
   ce dépôt sont installées.
4. Le rendre exploitable en CI : **exit 0** si le poste est conforme, **exit 1**
   avec un message qui nomme ce qui manque.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/installation-ansible/

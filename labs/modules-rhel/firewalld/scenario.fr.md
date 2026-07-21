# Contexte : ouvrir la stack web sans laisser la porte ouverte au reboot

L'application passe en production sur **web1.lab** ce soir : le site public en
HTTP et HTTPS, plus deux ports dont l'équipe de dev a encore besoin pour son
instance de staging. La mise en service précédente explique très bien pourquoi
plus personne ne fait confiance aux commandes de pare-feu tapées à la main. Les
règles avaient été appliquées à la console, avaient fonctionné tout l'après-midi,
et avaient disparu au reboot de maintenance : le site était injoignable à 6 h et
personne ne comprenait pourquoi. Vous refaites tout depuis **control-node.lab**.

Votre mission :

1. Vous assurer que firewalld est **installé, démarré et activé au boot** sur
   **web1.lab**, avant d'écrire la moindre règle dans le vide.
2. Autoriser les deux **services web prédéfinis** dans la zone publique, par
   leur nom de service plutôt que par des numéros de ports bruts.
3. Ouvrir les deux **ports custom du staging** dans la même zone.
4. Chaque règle doit être **active tout de suite et survivre au reboot** :
   n'obtenir que l'un des deux, c'est exactement le piège qui a fait tomber le
   site.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-firewalld/

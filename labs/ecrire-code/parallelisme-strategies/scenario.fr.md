# Contexte : les deux webservers sont tombés à la même seconde

Le dernier déploiement a coupé le site pendant quatre-vingt-dix secondes. Rien
n'a échoué : le playbook a simplement fait son travail sur **web1.lab** et
**web2.lab** en parallèle, et redémarré les deux en même temps. Derrière un
répartiteur de charge, deux nœuds sains mis à jour simultanément, cela fait
zéro nœud qui sert. La réponse n'est pas de tout ralentir : c'est de dire à
Ansible de parcourir le parc un hôte à la fois, et de s'arrêter net à la
première erreur plutôt que de casser le second nœud aussi. Vous corrigez ça
depuis **control-node.lab**.

Votre mission :

1. Cibler le groupe `webservers` et dérouler le play **un hôte à la fois**.
2. Régler la tolérance à zéro : le premier hôte en échec arrête le play avant
   qu'il ne touche le suivant.
3. Déposer un **marqueur** sur chaque hôte, et ralentir chaque lot juste assez
   pour que les deux dates de modification ne puissent pas se confondre. Le
   contenu du marqueur doit rester stable d'un run à l'autre : c'est sa date
   de modification qui témoigne, pas ce qu'il y a dedans.
4. Prouver la séquentialisation au lieu de la supposer : le marqueur de web1
   doit être strictement plus ancien que celui de web2. Lisez aussi la sortie :
   le bandeau `PLAY` apparaît désormais une fois par lot, pas une fois par run.
5. Rejouer le playbook sans rien changer : il ne doit plus rien modifier.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/parallelisme-strategies/

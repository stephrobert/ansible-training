# Contexte : remplacer les sleep aveugles qui tiennent le déploiement

Le playbook de déploiement de **db1.lab** est truffé de `sleep 30`, ajoutés
chacun le jour où quelque chose s'est mal passé. Personne n'ose les retirer, et
ils ne suffisent toujours pas : le traitement se termine parfois en deux
secondes, parfois en quarante, et le play continue sans se soucier de ce qui
s'est réellement produit. Attendre à l'aveugle n'est pas synchroniser. Vous
réécrivez la séquence depuis **control-node.lab** pour qu'elle attende des
**événements**, pas l'horloge.

Votre mission :

1. Sur **db1.lab**, lancer le traitement en arrière-plan qui pose son marqueur
   après quelques secondes, puis **attendre l'apparition du marqueur** avec un
   timeout qui échoue vite au lieu de patienter des minutes.
2. Ajouter une courte **pause de stabilisation**, le seul cas où un timer est
   honnête, en sachant qu'elle bloque le control node et non le managed node.
3. **Vérifier que le service écoute réellement** sur son port avant de déclarer
   le succès : un service `started` n'est pas toujours un service qui répond, et
   le module ne teste que le TCP.
4. Écrire le marqueur de succès une fois, et une seule, la synchronisation
   tenue.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-wait-for-pause/

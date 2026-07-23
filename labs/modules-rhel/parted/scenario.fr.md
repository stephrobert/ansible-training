# Contexte : découper le nouveau disque avant que le stockage ne le réclame

Un second disque vient d'être rattaché à **db1.lab** et il arrive brut : ni
label, ni partition. Le découpage cible est arrêté et vient de l'architecture :
une petite partition de boot EFI, une partition de taille fixe pour un système
de fichiers, et tout le reste confié à LVM pour que les volumes puissent grandir
plus tard. Ce qui compte autant que le découpage, c'est que ce playbook sera
rejoué, sur cet hôte et sur les vingt suivants : **un outil de partitionnement
qui se rejoue est un outil qui détruit des données**, sauf s'il reconnaît ce qui
existe déjà.

Votre mission :

1. Depuis **control-node.lab**, poser un **label GPT** sur le nouveau disque de
   **db1.lab**, puis tailler la **partition de boot de 500 Mio** avec les flags
   qu'exige une partition EFI.
2. Ajouter la **partition de 4 Gio** destinée à un système de fichiers, chaînée
   juste après la première, sans trou ni chevauchement.
3. Confier le **reste du disque** à une troisième partition marquée pour LVM,
   sans figer une taille qui casserait sur un disque de dimension différente.
4. Prouver l'**idempotence** : le second passage doit afficher `changed: 0`, et
   présenter la table obtenue avec ses flags.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-parted/

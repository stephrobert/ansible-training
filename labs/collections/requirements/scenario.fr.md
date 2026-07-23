# Contexte : un audit supply-chain tombe sur votre projet

L'équipe sécurité passe au crible tous les dépôts d'automatisation après qu'un
paquet compromis a frappé un autre service. La question posée au vôtre est
courte : pour chaque collection installée, d'où vient-elle, en quelle version
exacte, et comment savez-vous que les octets reçus sont ceux que le publieur a
signés ? La réponse honnête : certaines viennent de Galaxy public, une autre est
clonée depuis une branche Git qui bouge, et personne n'a jamais rien vérifié.

Votre mission, depuis **control-node.lab** :

1. Déclarer dans un manifeste unique toutes les collections du projet, couvrant
   plusieurs **natures de source** : Galaxy public, un dépôt Git, et au moins une
   autre, chacune avec son type explicite.
2. **Épingler strictement** : une version exacte ou un tag Git immuable. Une
   branche mouvante n'est pas une dépendance, c'est une promesse qu'un autre peut
   rompre.
3. Les installer dans un **chemin local au projet** plutôt que dans le home de
   l'utilisateur, pour un environnement reproductible et jetable, et prouver sur
   **db1.lab** ce qui a réellement été installé.
4. Vérifier l'intégrité de ce qui est descendu, et savoir tirer depuis plusieurs
   serveurs Galaxy le jour où l'entreprise place un hub privé devant le public.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/requirements-yml/

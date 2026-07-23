# Contexte : parler à l'API depuis le playbook, pas depuis un pipeline curl

La chaîne de déploiement doit enregistrer chaque serveur auprès d'une API
d'inventaire : lire la charge utile de référence, puis déclarer le nœud.
Aujourd'hui cela se fait en `command: curl` tuyauté dans `jq`, et cela fait mal.
Le code de retour ne dit rien d'utile sur le code HTTP, la réponse est analysée à
la regex, et toute API qui répond `201` au lieu de `200` casse l'exécution. Vous
réécrivez l'échange depuis **control-node.lab**, sur **db1.lab**, avec Ansible
qui analyse réellement le JSON au lieu d'un shell qui fait semblant.

Votre mission :

1. **Interroger l'endpoint de référence** en GET depuis **db1.lab**, en
   **capturant le corps de la réponse**, que le module ne renvoie pas par
   défaut, et l'enregistrer dans `/opt/`.
2. **Déclarer le nœud en POST** avec un **corps JSON** construit comme une
   structure, pas comme une chaîne échappée à la main.
3. **Accepter les codes légitimes de l'API** (`200` et `201`) : une création qui
   répond `201` est un succès, pas un échec.
4. Enregistrer la réponse **analysée** en JSON lisible, en partant de la
   structure que renvoie le module plutôt que du texte brut.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/reseau/module-uri/

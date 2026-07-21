# Contexte : un seul playbook, des hôtes qui ne se ressemblent pas

Le playbook doit tourner sur tout le parc, et le parc n'est pas homogène :
certains hôtes sont de la famille RedHat, d'autres non, certains tournent sur
une version trop ancienne pour la fonctionnalité, et une option ne doit être
activée que là où l'équipe l'a explicitement demandée. Aujourd'hui, il existe
trois playbooks quasi identiques, copiés-collés les uns des autres. Ils ont
divergé le jour où quelqu'un a corrigé un bug dans exactement l'un d'eux. Vous
ramenez la logique à un seul play sur `db1.lab`, piloté par des conditions.

Votre mission :

1. Conditionner une tâche sur un **fact** : elle s'applique à la famille
   RedHat et se saute partout ailleurs.
2. **Combiner deux conditions** pour la tâche liée à la version : la bonne
   distribution et un numéro de version assez élevé.
3. Traiter un drapeau qui peut ne pas exister du tout : vérifier qu'il est
   **défini** avant de le lire, puis le convertir, car un drapeau passé en
   ligne de commande est une chaîne, pas un booléen, et il est vrai dans les
   deux cas.
4. Prouver que le saut est propre : la tâche Debian doit être **skippée, pas en
   échec**, et son fichier ne doit exister nulle part sur db1.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/conditions-when/

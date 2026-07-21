# Contexte : un seul outil pour trouver le module, l'utiliser et vérifier l'inventaire

Votre équipe standardise sur l'**Automation content navigator**. L'ancien réflexe,
c'était `ansible-doc` ici, `ansible-inventory` là, `ansible-playbook` pour finir :
trois commandes, trois comportements, rien qui corresponde à ce que la production
exécute réellement (des Execution Environments). L'examen RHCE attend désormais que
vous dégainiez `ansible-navigator` pour toute la boucle.

Un collègue a besoin de poser un paramètre kernel sur **db1.lab** mais ne se
souvient plus quel module le fait, ni quelle collection le fournit. Plutôt que de
deviner, vous allez *trouver* le module avec le navigator, puis l'*utiliser*, puis
*valider* l'inventaire que le play va cibler, le tout avec le même outil.

Votre mission, depuis **control-node.lab** :

1. Utiliser `ansible-navigator doc` pour trouver le module qui gère les entrées
   `sysctl`, confirmer la collection dont il vient, et garder une **preuve** de
   cette exploration sur `db1.lab` (le nom pleinement qualifié du module doit y
   figurer).
2. Utiliser ce module découvert pour poser `vm.swappiness = 42` sur `db1.lab`, en
   live et persistant, de façon idempotente.
3. Écrire un petit inventaire et le valider avec `ansible-navigator inventory
   --list`, puis garder la sortie résolue comme preuve sur `db1.lab`.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/ansible-navigator/

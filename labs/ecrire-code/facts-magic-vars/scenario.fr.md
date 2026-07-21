# Contexte : le tableur d'inventaire auquel plus personne ne croit

Le rapport de capacité est un tableur, rempli à la main, et il est faux depuis
des mois : le chiffre de mémoire de db1 date d'avant son dernier
redimensionnement, et l'IP de web1 a bien été mise à jour lors du changement
de réseau, dans un des deux onglets. Pendant ce temps, les machines savent
tout cela d'elles-mêmes, et Ansible le collecte au début de chaque run avant
de le jeter. Depuis **control-node.lab**, vous construisez une synthèse qui lit
les machines plutôt que le tableur.

Votre mission :

1. Sur `db1.lab`, écrire `/tmp/facts-summary.txt` portant son nom d'inventaire,
   sa distribution et sa mémoire totale, **lus dans les facts** et non saisis à
   la main.
2. Y ajouter le nombre d'hôtes que contient réellement le groupe `webservers`,
   pris dans l'inventaire lui-même et non de mémoire.
3. Y ajouter l'**adresse IP de web1.lab** via `hostvars`, depuis un play qui
   tourne sur db1.
4. S'assurer que les facts de web1 existent avant de les lire : `hostvars` ne
   porte que ce qui a déjà été collecté. Puis réduire le coût de la collecte
   avec `gather_subset`.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/facts-magic-vars/

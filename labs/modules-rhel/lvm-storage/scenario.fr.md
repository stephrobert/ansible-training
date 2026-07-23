# Contexte : construire un stockage extensible sans fenêtre de maintenance

La dernière panne de **db1.lab** a servi de leçon : la partition de données était
pleine, et l'agrandir signifiait démonter, redimensionner et prier. L'équipe
d'architecture a tranché pour le prochain volume, ce sera LVM, précisément pour
que la croissance de demain coûte une commande au lieu d'un dimanche soir. Le
disque secondaire est rattaché et vierge. Vous construisez toute la chaîne
depuis **control-node.lab**, du volume physique jusqu'au volume monté, dans un
playbook que le parc rejouera.

Votre mission :

1. Sur **db1.lab**, faire du **disque secondaire un volume physique** et
   l'agréger dans un **volume group**, en une seule étape comme le permet le
   module dédié.
2. Tailler un **volume logique** dans ce groupe, en laissant de la place dans le
   pool pour la croissance qui justifie tout ce montage.
3. **Formater** le volume logique en xfs et le **monter via fstab**, avec
   l'option qui épargne au disque l'écriture des temps d'accès. Un volume monté
   à la main disparaît au redémarrage suivant, en silence.
4. Confirmer que le second passage affiche **`changed: 0`**.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/lvm-storage/

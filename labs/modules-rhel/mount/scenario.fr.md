# Contexte : donner à l'application un volume dédié qui revient après un reboot

L'application de **db1.lab** écrit ses données directement sur le système de
fichiers racine, et un log parti en vrille a déjà rempli le disque et arrêté le
système. Il lui faut son espace à elle, isolé, mais le disque physique n'arrivera
pas avant plusieurs semaines. Un fichier image monté en loop device achète
l'isolation tout de suite, sans attendre le matériel. La vraie exigence est celle
que tout le monde oublie : un volume monté à la main disparaît au reboot suivant,
et l'application se remet à écrire sur la racine sans prévenir.

Votre mission :

1. Sur **db1.lab**, créer le **fichier image de 100 Mo** de façon qu'un second
   passage ne le recrée pas, puis le **formater en ext4**.
2. Créer le point de montage, puis **monter l'image et l'inscrire dans
   `/etc/fstab`** en une seule étape : l'état que vous choisissez décide si le
   montage survit au reboot.
3. Passer l'option qui transforme le fichier image en device utilisable, et
   durcir le volume pour qu'il ne puisse porter **ni nœuds de périphériques ni
   binaires setuid**.
4. Prouver la persistance : l'entrée fstab est présente et le volume est monté
   maintenant.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-mount/

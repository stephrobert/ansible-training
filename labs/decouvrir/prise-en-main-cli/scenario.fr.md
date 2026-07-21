# Contexte : huit commandes, dont une qui vous évite la une des journaux

Première semaine dans l'équipe. En un après-midi, on vous demande ce que
résout vraiment un inventaire, quels arguments accepte réellement un module,
pourquoi le run de cette nuit a été lent, et où vit le mot de passe de la base
de production. Vous pourriez ouvrir huit onglets de navigateur. Ou apprendre
que chaque réponse est une **commande livrée avec Ansible**, et que la
dernière, `ansible-vault`, est tout ce qui sépare votre dépôt Git d'une fuite
de secrets. Tout se joue depuis **votre control node**.

Votre mission :

1. Faire le tour de la boîte à outils : `ansible` en ad-hoc, `ansible-doc`,
   `ansible-config`, `ansible-inventory`, `ansible-galaxy` et `ansible-lint`,
   chacun répondant à une vraie question.
2. Prouver ensuite que vous savez manipuler un secret : scripter la création
   d'un petit `vault-secret.yml` contenant une clé d'API et un mot de passe de
   base.
3. Le **chiffrer** avec un fichier de mot de passe en `0600`, et vérifier sur
   le disque que le fichier commence bien par l'en-tête Vault `AES256`.
4. Le **relire** sans le déchiffrer sur place, et échouer franchement
   (exit 1) au moindre écart.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/prise-en-main-cli/

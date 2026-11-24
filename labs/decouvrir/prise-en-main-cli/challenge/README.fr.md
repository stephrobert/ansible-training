# Huit commandes, dont une qui vous évite la une des journaux

## La situation

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
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/prise-en-main-cli/

## 🎯 Challenge — Chiffrer un secret avec ansible-vault

### ✅ Objectif

Écrire un script Bash `solution.sh` à la racine de **ce répertoire** qui :

1. Crée un fichier `vault-secret.yml` contenant exactement :

   ```yaml
   api_key: secret-RHCE-2026
   db_password: motdepasse123
   ```

2. Le chiffre avec **`ansible-vault encrypt`** en utilisant un mot de passe fourni
   via `--vault-password-file`. Le mot de passe est écrit dans `.vault-pass`
   (gitignored).

3. **Vérifie** que le fichier chiffré commence par `$ANSIBLE_VAULT;1.1;AES256`.

4. **Déchiffre** le fichier (lecture via `ansible-vault view --vault-password-file
   .vault-pass`) et vérifie que la clé `api_key: secret-RHCE-2026` est bien
   présente dans la sortie.

5. Exit 0 si tout marche, exit 1 sinon.

Squelette à compléter :

```bash
#!/usr/bin/env bash
set -euo pipefail

VAULT_PASS_FILE="$(dirname "$0")/.vault-pass"
SECRET_FILE="$(dirname "$0")/vault-secret.yml"

# 1. Poser le mot de passe vault dans .vault-pass (un mot de passe au choix)
echo "???" > "$VAULT_PASS_FILE"

# 2. Créer le fichier en clair (heredoc avec api_key + db_password)
cat > "$SECRET_FILE" <<'EOF'
???
EOF

# 3. Le chiffrer avec ansible-vault (utiliser la sous-commande appropriée)
ansible-vault ??? "$SECRET_FILE" --vault-password-file "$VAULT_PASS_FILE"

# 4. Vérifier que la première ligne est bien le header AES256
head -1 "$SECRET_FILE" | grep -q '^\$ANSIBLE_VAULT;1.1;AES256$' \
  || { echo "FAIL : header Vault invalide"; exit 1; }

# 5. Lire le contenu déchiffré et vérifier que la clé api_key est présente
ansible-vault ??? "$SECRET_FILE" --vault-password-file "$VAULT_PASS_FILE" \
  | grep -q '???' \
  || { echo "FAIL : déchiffrement KO"; exit 1; }

echo "Vault OK"
```

> 💡 **Pièges** :
>
> - `.vault-pass` doit être en mode `0600` (sinon avertissement Ansible).
> - Le YAML doit avoir la structure `clé: valeur` exactement comme demandé.
> - `ansible-vault` a 5 sous-commandes principales : `encrypt`, `decrypt`,
>   `view`, `edit`, `rekey`. Choisissez celle qui **lit sans modifier le
>   fichier** pour l'étape 5.

### 🧪 Validation

Le test pytest lance votre `solution.sh` et vérifie qu'il retourne exit 0
ET que `vault-secret.yml` est bien chiffré sur disque.

```bash
pytest -v labs/decouvrir/prise-en-main-cli/challenge/tests/
```

### 🚀 Pour aller plus loin

- Au lieu de poser le mot de passe en clair dans `.vault-pass`, intégrez-le
  via le **client de récupération de mot de passe** (un script qui lit dans
  un keyring système).
- Ajoutez **`ansible-vault rekey`** pour changer le mot de passe d'un fichier
  Vault sans toucher au contenu.

### 🧹 Reset

Pour rejouer le challenge dans un état neutre :

```bash
dsoxlab clean decouvrir-prise-en-main-cli
```

Cette cible désinstalle/supprime ce que la solution a posé sur les managed
nodes (paquets, fichiers, services, règles firewall) afin que vous puissiez
relancer la solution from scratch.

#!/usr/bin/env bash
# Pose les mots de passe vault que les labs attendent.
#
# POURQUOI CE SCRIPT
#
# Les fichiers `.vault_password` des labs sont gitignorés : on ne commite pas un
# mot de passe, même pédagogique. Résultat, ils sont ABSENTS de tout clone, et
# les labs vault comme le capstone RHCE sont injouables tant que personne ne les
# recrée. Le run de validation le montre sans ambiguïté :
#
#   [WARNING]: The vault password file labs/vault/dans-roles/.vault_password
#              was not found
#
# Ce ne sont pas de vrais secrets : ce sont des mots de passe D'EXERCICE, chacun
# documenté dans le README de son lab (« echo "vault-roles-2026" > … ») et dans
# le CREDENTIALS.txt du formateur. Les fichiers de variables chiffrés livrés
# avec les labs le sont AVEC ces mots de passe : ils sont donc imposés, pas
# choisis.
#
# À ne pas confondre avec `.vault-pass` (à la racine) : celui-là est le mot de
# passe FORMATEUR, il chiffre les solutions de référence, et lui reste un vrai
# secret qui n'a rien à faire ici.
#
# Usage :
#   scripts/setup-lab-vault-passwords.sh          # pose ce qui manque
#
# NOTE : ce script était documenté comme « mise run bootstrap-vault ». Cette
# tâche n'existe pas dans mise.toml : la seule invocation qui marche est le
# chemin direct ci-dessus. Les README des labs vault ont été alignés dessus.

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${LAB_DIR}"

log() { echo -e "\033[0;34m[vault]\033[0m $*"; }
ok()  { echo -e "\033[0;32m[OK]\033[0m $*"; }

# <chemin relatif>|<mot de passe documenté dans le README du lab>
PASSWORDS=(
  # Ce lab ne livre AUCUN fichier chiffré : l'apprenant chiffre le sien avec ce
  # mot de passe pendant le challenge. Rien à ouvrir, donc rien à perdre.
  "labs/premiers-pas/ansible-vault/challenge/.vault_password|premiers-pas-vault-2026"
  "labs/vault/introduction/.vault_password|lab77-vault-2026"
  "labs/vault/chiffrer-fichier-variable/.vault_password|lab78-vault-2026"
  "labs/vault/id-multiples/.vault_password_dev|vault-dev-2026"
  "labs/vault/id-multiples/.vault_password_prod|vault-prod-2026"
  # Le README du lab annonce « vault-mixte-2026 » : c'est FAUX, ses fichiers
  # s'ouvrent avec lab80-vault-2026 (vérifié, et conforme au CREDENTIALS.txt).
  "labs/vault/playbooks-mixtes/.vault_password|lab80-vault-2026"
  # Idem : le README annonce « vault-roles-2026 », les fichiers s'ouvrent
  # avec lab81-vault-2026.
  "labs/vault/dans-roles/.vault_password|lab81-vault-2026"
  "labs/rhce/mock-ex294/.vault_password|monMotDePasseLab92"
  "labs/rhce/mock-ex294-2/.vault_password|monMotDePasseLab200"
)

created=0
kept=0
for entry in "${PASSWORDS[@]}"; do
    path="${entry%%|*}"
    secret="${entry#*|}"
    dir="$(dirname "${path}")"

    if [[ ! -d "${dir}" ]]; then
        echo "  ignoré (lab absent) : ${path}" >&2
        continue
    fi
    # Ne jamais écraser : l'apprenant a pu en choisir un autre et rechiffrer
    # ses propres fichiers avec.
    if [[ -f "${path}" ]]; then
        kept=$((kept + 1))
        continue
    fi
    printf '%s' "${secret}" > "${path}"
    chmod 0600 "${path}"
    created=$((created + 1))
done

log "${created} posé(s), ${kept} déjà présent(s)"
ok "les labs vault ont leur mot de passe d'exercice"

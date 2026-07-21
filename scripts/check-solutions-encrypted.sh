#!/usr/bin/env bash
# Refuse tout fichier de solution/ qui ne serait pas chiffré par ansible-vault.
#
# La solution de référence d'un lab n'a de valeur que tant qu'elle n'est pas
# lisible : une solution commitée en clair spoile le lab pour tout le monde, et
# l'historique git la garde même après suppression. Ce hook vérifie l'en-tête de
# chiffrement plutôt que de faire confiance à l'auteur.
#
# Chiffrer / déchiffrer :
#   ansible-vault encrypt --vault-password-file .vault-pass <fichier>
#   ansible-vault decrypt --vault-password-file .vault-pass <fichier>

set -euo pipefail

readonly VAULT_HEADER='$ANSIBLE_VAULT'
readonly SOLUTION_DIR='solution'

[ -d "$SOLUTION_DIR" ] || exit 0

clear_files=()

# Ne contrôle que ce que git suit : les fichiers non suivis ne partiront pas
# dans un commit, et .gitkeep / .gitignore n'ont rien à chiffrer.
while IFS= read -r file; do
    case "${file##*/}" in
        .gitkeep | .gitignore) continue ;;
    esac
    [ -s "$file" ] || continue

    if ! head -c "${#VAULT_HEADER}" -- "$file" | grep -qF -- "$VAULT_HEADER"; then
        clear_files+=("$file")
    fi
done < <(git ls-files -z -- "$SOLUTION_DIR" | tr '\0' '\n')

if [ ${#clear_files[@]} -gt 0 ]; then
    echo "ERREUR : ces fichiers de solution/ ne sont pas chiffrés :" >&2
    printf '  %s\n' "${clear_files[@]}" >&2
    cat >&2 <<'EOF'

Une solution en clair spoile le lab, et l'historique git la conserve.
Chiffre-les avant de committer :

  ansible-vault encrypt --vault-password-file .vault-pass <fichier>
EOF
    exit 1
fi

exit 0

#!/usr/bin/env bash
# Affiche l'état (chiffré/clair) de chaque fichier du dossier solution/.
# Utile pour vérifier avant un commit.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOLUTION_DIR="${REPO_ROOT}/solution"

if [[ ! -d "$SOLUTION_DIR" ]]; then
    echo "Aucun dossier solution/."
    exit 0
fi

# Tous les fichiers de solution/ doivent être chiffrés, peu importe leur
# extension (un lab peut livrer un .py, .cfg, .md, .conf, etc.). On exclut
# uniquement les fichiers binaires/auto-générés qui ne contiennent pas de
# code apprenant.
mapfile -t FILES < <(find "$SOLUTION_DIR" -type f \
    ! -name ".gitkeep" \
    ! -name "*.png" ! -name "*.jpg" ! -name "*.jpeg" ! -name "*.gif" \
    ! -name "*.tar.gz" ! -name "*.zip" \
    | sort)

n_locked=0
n_clear=0

for f in "${FILES[@]}"; do
    rel="${f#${REPO_ROOT}/}"
    if head -1 "$f" 2>/dev/null | grep -q '^\$ANSIBLE_VAULT'; then
        echo "  🔒 ${rel}"
        n_locked=$((n_locked + 1))
    else
        echo "  📄 ${rel}"
        n_clear=$((n_clear + 1))
    fi
done

echo ""
echo "Total : ${n_locked} chiffré(s), ${n_clear} en clair sur ${#FILES[@]}."

if [[ $n_clear -gt 0 ]]; then
    echo ""
    echo "⚠️  Lance 'make solutions-lock' avant de commiter !"
    exit 1
fi

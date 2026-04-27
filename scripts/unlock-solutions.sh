#!/usr/bin/env bash
# Déchiffre tous les fichiers du dossier solution/ avec ansible-vault.
#
# Les fichiers en clair sont skippés.
# Mot de passe : .vault-pass à la racine.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT_PASS="${REPO_ROOT}/.vault-pass"
SOLUTION_DIR="${REPO_ROOT}/solution"

if [[ ! -f "$VAULT_PASS" ]]; then
    echo "ERREUR : ${VAULT_PASS} introuvable." >&2
    exit 1
fi

mapfile -t FILES < <(find "$SOLUTION_DIR" -type f \
    \( -name "*.yml" -o -name "*.yaml" -o -name "*.sh" -o -name "*.j2" -o -name "*.txt" \) \
    | sort)

if [[ ${#FILES[@]} -eq 0 ]]; then
    echo "[unlock] Aucun fichier dans ${SOLUTION_DIR}/"
    exit 0
fi

n_unlocked=0
n_skipped=0
n_total=${#FILES[@]}

for f in "${FILES[@]}"; do
    rel="${f#${REPO_ROOT}/}"
    if ! head -1 "$f" | grep -q '^\$ANSIBLE_VAULT'; then
        echo "  SKIP    ${rel} (déjà en clair)"
        n_skipped=$((n_skipped + 1))
        continue
    fi
    if ansible-vault decrypt --vault-password-file "$VAULT_PASS" "$f" >/dev/null 2>&1; then
        echo "  UNLOCK  ${rel}"
        n_unlocked=$((n_unlocked + 1))
    else
        echo "  FAIL    ${rel}" >&2
    fi
done

echo ""
echo "[unlock] ${n_unlocked} fichier(s) déchiffré(s), ${n_skipped} déjà en clair sur ${n_total} total."
echo ""
echo "⚠️  Pense à relancer 'make solutions-lock' avant de commiter."

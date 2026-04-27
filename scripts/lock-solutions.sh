#!/usr/bin/env bash
# Chiffre tous les fichiers du dossier solution/ avec ansible-vault.
#
# Sont chiffrés : *.yml, *.yaml, *.sh, *.j2, *.txt sous solution/.
# Les fichiers déjà chiffrés (header $ANSIBLE_VAULT) sont skippés.
#
# Mot de passe : .vault-pass à la racine (gitignored).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT_PASS="${REPO_ROOT}/.vault-pass"
SOLUTION_DIR="${REPO_ROOT}/solution"

if [[ ! -f "$VAULT_PASS" ]]; then
    echo "ERREUR : ${VAULT_PASS} introuvable." >&2
    echo "Crée-le avec un mot de passe (puis chmod 600) avant de lancer ce script." >&2
    exit 1
fi

if [[ ! -d "$SOLUTION_DIR" ]]; then
    echo "ERREUR : ${SOLUTION_DIR} introuvable." >&2
    exit 1
fi

# Trouve tous les fichiers à chiffrer.
mapfile -t FILES < <(find "$SOLUTION_DIR" -type f \
    \( -name "*.yml" -o -name "*.yaml" -o -name "*.sh" -o -name "*.j2" -o -name "*.txt" \) \
    | sort)

if [[ ${#FILES[@]} -eq 0 ]]; then
    echo "[lock] Aucun fichier à chiffrer dans ${SOLUTION_DIR}/"
    exit 0
fi

n_locked=0
n_skipped=0
n_total=${#FILES[@]}

for f in "${FILES[@]}"; do
    rel="${f#${REPO_ROOT}/}"
    # Skip si déjà chiffré (header $ANSIBLE_VAULT)
    if head -1 "$f" | grep -q '^\$ANSIBLE_VAULT'; then
        echo "  SKIP  ${rel} (déjà chiffré)"
        n_skipped=$((n_skipped + 1))
        continue
    fi
    if ansible-vault encrypt --vault-password-file "$VAULT_PASS" "$f" >/dev/null 2>&1; then
        echo "  LOCK  ${rel}"
        n_locked=$((n_locked + 1))
    else
        echo "  FAIL  ${rel}" >&2
    fi
done

echo ""
echo "[lock] ${n_locked} fichier(s) chiffré(s), ${n_skipped} déjà chiffré(s) sur ${n_total} total."

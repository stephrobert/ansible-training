#!/usr/bin/env bash
# Déchiffre la solution officielle d'un lab et la copie dans
# labs/<section>/<lab>/challenge/ pour permettre de jouer/tester directement.
#
# Usage : scripts/solve.sh <section>/<lab>
# Ex    : scripts/solve.sh ecrire-code/handlers
#
# Mot de passe : .vault-pass à la racine.

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage : $0 <section>/<lab>" >&2
    echo "Exemple : $0 ecrire-code/handlers" >&2
    echo "" >&2
    echo "Astuce : 'find labs -mindepth 2 -maxdepth 2 -type d | sort' pour lister les chemins." >&2
    exit 1
fi

LAB_PATH="$1"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT_PASS="${REPO_ROOT}/.vault-pass"

if [[ ! -f "$VAULT_PASS" ]]; then
    echo "ERREUR : ${VAULT_PASS} introuvable." >&2
    exit 1
fi

SRC_DIR="${REPO_ROOT}/solution/${LAB_PATH}"
DST_LAB="${REPO_ROOT}/labs/${LAB_PATH}"

if [[ ! -d "$SRC_DIR" ]]; then
    echo "ERREUR : aucune archive de solution dans ${SRC_DIR}." >&2
    echo "Astuce : 'find solution -mindepth 2 -maxdepth 2 -type d | sort' pour lister." >&2
    exit 1
fi

if [[ ! -d "$DST_LAB" ]]; then
    echo "ERREUR : aucun lab ${DST_LAB}." >&2
    exit 1
fi
DST_DIR="${DST_LAB}/challenge"

# Synchronise les fichiers utiles du solution/<path> vers labs/<path>/challenge/.
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

cp -r "$SRC_DIR/." "$TMP/"

# Déchiffrer in-place dans le dossier temporaire
mapfile -t FILES < <(find "$TMP" -type f \
    \( -name "*.yml" -o -name "*.yaml" -o -name "*.sh" -o -name "*.j2" -o -name "*.txt" \))

for f in "${FILES[@]}"; do
    if head -1 "$f" | grep -q '^\$ANSIBLE_VAULT'; then
        ansible-vault decrypt --vault-password-file "$VAULT_PASS" "$f" >/dev/null 2>&1 \
            || { echo "FAIL : déchiffrement de $f" >&2; exit 1; }
    fi
done

# Copier vers labs/<path>/challenge/
mkdir -p "$DST_DIR"
cp -r "$TMP/." "$DST_DIR/"

if [[ -f "$DST_DIR/solution.sh" ]]; then
    chmod +x "$DST_DIR/solution.sh"
fi

echo "[solve] Solution lab '${LAB_PATH}' déchiffrée + posée dans :"
echo "        ${DST_DIR#${REPO_ROOT}/}/"
ls -la "$DST_DIR" | grep -E "solution|files|templates|vars" | sed 's|^|        |'
echo ""
echo "Lance maintenant : pytest -v labs/${LAB_PATH}/challenge/tests/"

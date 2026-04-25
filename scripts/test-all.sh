#!/usr/bin/env bash
# Exécute `make verify` dans chaque sous-dossier de labs/.
# En phase 0, labs/ est vide donc le script retourne vert immédiatement.
# Critère de sortie roadmap §9.

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABS_ROOT="${LAB_DIR}/labs"

log()  { echo -e "\033[0;34m[test-all]\033[0m $*"; }
ok()   { echo -e "\033[0;32m[OK]\033[0m $*"; }
fail() { echo -e "\033[0;31m[FAIL]\033[0m $*" >&2; }

# Si pas de labs ou aucun Makefile, sortie verte (c'est l'état attendu en phase 0)
mapfile -t LAB_DIRS < <(find "${LABS_ROOT}" -mindepth 2 -maxdepth 4 -type f -name Makefile -printf '%h\n' 2>/dev/null | sort)

if [[ ${#LAB_DIRS[@]} -eq 0 ]]; then
    ok "Aucun lab unitaire à exécuter (phase 0 — labs/ vide est l'état attendu)"
    exit 0
fi

log "Exécution de ${#LAB_DIRS[@]} lab(s) unitaire(s)..."
FAILED=()

for d in "${LAB_DIRS[@]}"; do
    log "→ ${d}"
    if (cd "${d}" && make setup run verify clean) >/dev/null 2>&1; then
        ok "${d}"
    else
        fail "${d}"
        FAILED+=("${d}")
    fi
done

echo ""
if [[ ${#FAILED[@]} -eq 0 ]]; then
    ok "Tous les labs passent (${#LAB_DIRS[@]} ok)"
    exit 0
else
    fail "${#FAILED[@]} lab(s) en échec :"
    printf '  - %s\n' "${FAILED[@]}"
    exit 1
fi

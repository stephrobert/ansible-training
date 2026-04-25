#!/usr/bin/env bash
# Convertit en batch les fichiers .excalidraw de src-schema/ansible/ en SVG
# stockés dans src/assets/ansible/<section>/. Utilise Kroki local (port 8000)
# qui est l'outil canonique du blog stephane-robert.info pour Excalidraw → SVG.
#
# Usage : ./scripts/export-schemas.sh <chemin-vers-blog-stephane-robert>
# Note : ce script ne tourne pas dans le lab Ansible mais dans le repo Astro.
# Il est conservé ici par cohérence avec la roadmap §11.

set -euo pipefail

BLOG_DIR="${1:-${HOME}/Projets/test-astro-5}"
KROKI_URL="${KROKI_SERVER:-http://localhost:8000}"

log()  { echo -e "\033[0;34m[export-schemas]\033[0m $*"; }
ok()   { echo -e "\033[0;32m[OK]\033[0m $*"; }
fail() { echo -e "\033[0;31m[FAIL]\033[0m $*" >&2; exit 1; }

[[ -d "${BLOG_DIR}" ]] || fail "Repo Astro introuvable : ${BLOG_DIR}"
[[ -d "${BLOG_DIR}/src-schema/ansible" ]] || { log "Pas encore de src-schema/ansible/ — rien à exporter"; exit 0; }

# Vérification Kroki actif
if ! curl -sf "${KROKI_URL}/health" >/dev/null 2>&1; then
    fail "Kroki indisponible sur ${KROKI_URL} — démarre-le depuis ${HOME}/Projets/kroki-local/docker-compose.yml"
fi

cd "${BLOG_DIR}"

mapfile -t SOURCES < <(find src-schema/ansible -name "*.excalidraw" 2>/dev/null)
[[ ${#SOURCES[@]} -gt 0 ]] || { log "Aucun .excalidraw à convertir"; exit 0; }

for SRC in "${SOURCES[@]}"; do
    REL="${SRC#src-schema/ansible/}"
    SECTION="$(dirname "${REL}")"
    NAME="$(basename "${REL}" .excalidraw)"

    DEST_DIR="src/assets/ansible/${SECTION}"
    DEST="${DEST_DIR}/${NAME}.svg"

    mkdir -p "${DEST_DIR}"

    log "→ ${SRC}  →  ${DEST}"
    curl -sf -X POST "${KROKI_URL}/excalidraw/svg" \
        -H "Content-Type: text/plain" \
        --data-binary "@${SRC}" \
        -o "${DEST}" \
        || { fail "Conversion échouée : ${SRC}"; continue; }
done

ok "Export terminé."

#!/usr/bin/env bash
# Restaure les 4 VMs du lab depuis un snapshot libvirt.
# Si SNAPSHOT_NAME n'est pas passé, utilise le snapshot le plus récent
# qui matche tous les VMs (le préfixe "lab-checkpoint-" l'identifie).

set -euo pipefail

VM_NAMES=(control-node web1 web2 db1)

log()  { echo -e "\033[0;34m[restore]\033[0m $*"; }
ok()   { echo -e "\033[0;32m[OK]\033[0m $*"; }
fail() { echo -e "\033[0;31m[FAIL]\033[0m $*" >&2; exit 1; }

if [[ -z "${SNAPSHOT_NAME:-}" ]]; then
    # Cherche le dernier snapshot du control-node comme référence
    SNAPSHOT_NAME=$(virsh snapshot-list control-node --name 2>/dev/null \
        | grep -E '^lab-checkpoint-' | sort | tail -1 || true)
    [[ -n "${SNAPSHOT_NAME}" ]] || fail "Aucun snapshot 'lab-checkpoint-*' trouvé"
    log "Utilisation du snapshot le plus récent : ${SNAPSHOT_NAME}"
fi

for NAME in "${VM_NAMES[@]}"; do
    if virsh dominfo "${NAME}" >/dev/null 2>&1; then
        log "Restore ${NAME}/${SNAPSHOT_NAME}..."
        sudo virsh snapshot-revert --domain "${NAME}" --snapshotname "${SNAPSHOT_NAME}" --running
        ok "${NAME}"
    fi
done

ok "Toutes les VMs restaurées depuis ${SNAPSHOT_NAME}."

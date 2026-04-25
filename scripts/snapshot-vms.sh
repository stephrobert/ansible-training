#!/usr/bin/env bash
# Snapshot externe libvirt sur les 4 VMs du lab.
# Utilisable avant un test risqué (modif SELinux, partitionnement, réseau).

set -euo pipefail

VM_NAMES=(control-node web1 web2 db1)
SNAPSHOT_NAME="lab-checkpoint-$(date +%Y%m%d-%H%M%S)"

log()  { echo -e "\033[0;34m[snapshot]\033[0m $*"; }
ok()   { echo -e "\033[0;32m[OK]\033[0m $*"; }

for NAME in "${VM_NAMES[@]}"; do
    if virsh dominfo "${NAME}" >/dev/null 2>&1; then
        log "Snapshot ${NAME}/${SNAPSHOT_NAME}..."
        sudo virsh snapshot-create-as --domain "${NAME}" --name "${SNAPSHOT_NAME}" --atomic
        ok "${NAME}"
    fi
done

ok "Snapshot ${SNAPSHOT_NAME} pris sur toutes les VMs présentes."
echo "Pour restaurer : SNAPSHOT_NAME=${SNAPSHOT_NAME} ./scripts/restore-vms.sh"

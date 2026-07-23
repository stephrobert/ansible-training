#!/usr/bin/env bash
# Snapshot externe libvirt sur les 4 VMs du lab.
# Utilisable avant un test risqué (modif SELinux, partitionnement, réseau).

set -euo pipefail

# CE SCRIPT NE PRÉPARE PAS L'ISOLATION DES LABS. Pour cela : mise run rebase.
#
# Les noms portaient l'ancienne convention (control-node) alors que les
# domaines s'appellent control-node.lab depuis le passage à dsoxlab : la boucle
# ne trouvait plus aucune VM, n'en snapshotait aucune, et affichait quand même
# « Snapshot pris sur toutes les VMs présentes ». Ce faux positif a coûté deux
# passes de validation, en laissant croire que l'état de base était figé.
VM_NAMES=(control-node.lab web1.lab web2.lab db1.lab)
SNAPSHOT_NAME="lab-checkpoint-$(date +%Y%m%d-%H%M%S)"

log()  { echo -e "\033[0;34m[snapshot]\033[0m $*"; }
ok()   { echo -e "\033[0;32m[OK]\033[0m $*"; }
fail() { echo -e "\033[0;31m[FAIL]\033[0m $*" >&2; }

found=0
for NAME in "${VM_NAMES[@]}"; do
    if sudo virsh dominfo "${NAME}" >/dev/null 2>&1; then
        found=$((found + 1))
        log "Snapshot ${NAME}/${SNAPSHOT_NAME}..."
        sudo virsh snapshot-create-as --domain "${NAME}" --name "${SNAPSHOT_NAME}" --atomic
        ok "${NAME}"
    fi
done

if [[ "${found}" -eq 0 ]]; then
    fail "aucun des domaines ${VM_NAMES[*]} n'existe : rien n'a été snapshoté."
    fail "Les VM sont-elles provisionnées ? (dsoxlab status)"
    exit 1
fi

ok "Snapshot ${SNAPSHOT_NAME} pris sur ${found} VM."
echo "Pour restaurer : SNAPSHOT_NAME=${SNAPSHOT_NAME} ./scripts/restore-vms.sh"
echo "Rappel : ceci ne prépare PAS l'isolation des labs. Pour cela, mise run rebase."

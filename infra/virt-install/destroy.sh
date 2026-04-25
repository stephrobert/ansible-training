#!/usr/bin/env bash
# Détruit les VMs et le réseau libvirt du lab Ansible.
# Conserve l'image cloud AlmaLinux (mutualisable entre runs).

set -euo pipefail

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$(cd "${INFRA_DIR}/../.." && pwd)"
CLOUD_INIT_DIR="${INFRA_DIR}/cloud-init"

VM_NAMES=(control-node web1 web2 db1)
NETWORK_NAME="lab-ansible"

log()  { echo -e "\033[0;34m[destroy]\033[0m $*"; }
ok()   { echo -e "\033[0;32m[OK]\033[0m $*"; }
warn() { echo -e "\033[0;33m[WARN]\033[0m $*"; }

# ----- Confirmation interactive -----
if [[ -t 0 ]] && [[ "${FORCE_DESTROY:-0}" != "1" ]]; then
    read -p "Détruire les 4 VMs et le réseau ${NETWORK_NAME} ? (y/N) " -n 1 -r
    echo
    [[ "${REPLY}" =~ ^[Yy]$ ]] || { log "Annulé"; exit 0; }
fi

# ----- Suppression VMs -----
for NAME in "${VM_NAMES[@]}"; do
    if virsh dominfo "${NAME}" >/dev/null 2>&1; then
        log "Arrêt + suppression de ${NAME}..."
        virsh destroy "${NAME}" >/dev/null 2>&1 || true
        virsh undefine "${NAME}" --remove-all-storage >/dev/null 2>&1 \
            || virsh undefine "${NAME}" >/dev/null 2>&1 || true
        ok "${NAME} supprimée"
    else
        log "${NAME} n'existe pas"
    fi
done

# ----- Disques résiduels -----
for NAME in "${VM_NAMES[@]}"; do
    DISK="/var/lib/libvirt/images/${NAME}.qcow2"
    [[ -f "${DISK}" ]] && { sudo rm -f "${DISK}"; ok "Disque ${DISK} supprimé"; }
done

# ----- ISOs cloud-init -----
for NAME in "${VM_NAMES[@]}"; do
    SEED_DIR="${CLOUD_INIT_DIR}/${NAME}"
    [[ -d "${SEED_DIR}" ]] && { rm -rf "${SEED_DIR}"; ok "Cloud-init ${NAME} supprimé"; }
done

# ----- Réseau libvirt -----
if virsh net-info "${NETWORK_NAME}" >/dev/null 2>&1; then
    log "Arrêt + suppression du réseau ${NETWORK_NAME}..."
    sudo virsh net-destroy "${NETWORK_NAME}" >/dev/null 2>&1 || true
    sudo virsh net-undefine "${NETWORK_NAME}" >/dev/null 2>&1 || true
    ok "Réseau ${NETWORK_NAME} supprimé"
fi

# ----- known_hosts -----
log "Nettoyage de ~/.ssh/known_hosts pour les IPs du lab..."
for IP in 10.10.20.10 10.10.20.21 10.10.20.22 10.10.20.31; do
    ssh-keygen -R "${IP}" >/dev/null 2>&1 || true
done

echo ""
ok "Lab détruit. L'image cloud AlmaLinux est conservée pour réutilisation."

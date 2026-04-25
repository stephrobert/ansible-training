#!/usr/bin/env bash
# Provisionne les 4 VMs du lab Ansible RHCE :
#   - control-node.lab  (10.10.20.10)
#   - web1.lab          (10.10.20.21)
#   - web2.lab          (10.10.20.22)
#   - db1.lab           (10.10.20.31)
#
# Image cloud : AlmaLinux 10 (x86_64) téléchargée et mise en backing file
# Réseau libvirt : lab-ansible (10.10.20.0/24, NAT, DNS dnsmasq libvirt)

set -euo pipefail

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$(cd "${INFRA_DIR}/../.." && pwd)"
CLOUD_INIT_DIR="${INFRA_DIR}/cloud-init"

# -------------------------- Variables ---------------------------------
ALMA_IMAGE_URL="https://repo.almalinux.org/almalinux/10/cloud/x86_64/images/AlmaLinux-10-GenericCloud-latest.x86_64.qcow2"
ALMA_IMAGE_NAME="AlmaLinux-10-GenericCloud-latest.x86_64.qcow2"

IMAGES_DIR="/var/lib/libvirt/images"
BASE_IMAGE_PATH="${IMAGES_DIR}/${ALMA_IMAGE_NAME}"

NETWORK_NAME="lab-ansible"
NETWORK_CIDR="10.10.20.0/24"
NETWORK_GATEWAY="10.10.20.1"
NETWORK_DHCP_START="10.10.20.100"
NETWORK_DHCP_END="10.10.20.200"

# Hôte par hôte : nom, IP, MAC, RAM, vCPU, disque, template user-data.
# Les MACs sont déterministes (préfixe libvirt 52:54:00:ab + suffixe = IP)
# pour permettre des baux DHCP statiques côté réseau libvirt. Cloud-init
# n'a alors pas besoin de configurer une IP statique : l'IP est imposée
# par le réseau au lease DHCP. C'est la stratégie la plus robuste pour
# AlmaLinux 10 / RHEL 10 (qui utilisent NetworkManager, pas Netplan).
declare -a VMS=(
  "control-node|10.10.20.10|52:54:00:ab:00:10|2048|2|20|control-node"
  "web1|10.10.20.21|52:54:00:ab:00:21|1024|1|10|managed-node"
  "web2|10.10.20.22|52:54:00:ab:00:22|1024|1|10|managed-node"
  "db1|10.10.20.31|52:54:00:ab:00:31|1536|1|15|managed-node"
)

SSH_PUBKEY_FILE="${LAB_DIR}/ssh/id_ed25519.pub"

# -------------------------- Helpers -----------------------------------
log()  { echo -e "\033[0;34m[provision]\033[0m $*"; }
ok()   { echo -e "\033[0;32m[OK]\033[0m $*"; }
warn() { echo -e "\033[0;33m[WARN]\033[0m $*"; }
fail() { echo -e "\033[0;31m[FAIL]\033[0m $*" >&2; exit 1; }

# -------------------------- Pré-requis --------------------------------
[[ -f "${SSH_PUBKEY_FILE}" ]] || fail "Clé SSH publique absente : ${SSH_PUBKEY_FILE} — lance d'abord 'make bootstrap'"

for cmd in virsh virt-install qemu-img cloud-localds wget; do
    command -v "${cmd}" >/dev/null 2>&1 || fail "Commande requise manquante : ${cmd}"
done

# -------------------------- Réseau libvirt ----------------------------
if virsh net-info "${NETWORK_NAME}" >/dev/null 2>&1; then
    NET_STATE=$(virsh net-info "${NETWORK_NAME}" | awk '/^Active:/ {print $2}')
    if [[ "${NET_STATE}" != "yes" ]]; then
        log "Activation du réseau libvirt ${NETWORK_NAME}..."
        sudo virsh net-start "${NETWORK_NAME}"
    fi
    ok "Réseau libvirt '${NETWORK_NAME}' actif"
else
    log "Création du réseau libvirt '${NETWORK_NAME}' (${NETWORK_CIDR}) avec baux DHCP statiques..."

    # Construit la liste des baux statiques <host> à partir du tableau VMS
    HOST_ENTRIES=""
    for entry in "${VMS[@]}"; do
        IFS='|' read -r NAME IP MAC _ _ _ _ <<< "${entry}"
        HOST_ENTRIES+=$'\n      '"<host mac='${MAC}' name='${NAME}' ip='${IP}'/>"
    done

    NET_XML="$(mktemp)"
    cat > "${NET_XML}" <<EOF
<network>
  <name>${NETWORK_NAME}</name>
  <forward mode='nat'/>
  <bridge name='virbr-ansible' stp='on' delay='0'/>
  <domain name='lab' localOnly='yes'/>
  <ip address='${NETWORK_GATEWAY}' netmask='255.255.255.0'>
    <dhcp>
      <range start='${NETWORK_DHCP_START}' end='${NETWORK_DHCP_END}'/>${HOST_ENTRIES}
    </dhcp>
  </ip>
</network>
EOF
    sudo virsh net-define "${NET_XML}"
    sudo virsh net-start "${NETWORK_NAME}"
    sudo virsh net-autostart "${NETWORK_NAME}"
    rm -f "${NET_XML}"
    ok "Réseau '${NETWORK_NAME}' créé avec 4 baux DHCP statiques"
fi

# -------------------------- Image AlmaLinux 10 ------------------------
if [[ -f "${BASE_IMAGE_PATH}" ]]; then
    ok "Image AlmaLinux 10 déjà présente : ${BASE_IMAGE_PATH}"
else
    log "Téléchargement AlmaLinux 10 cloud image..."
    sudo wget --progress=dot:giga -O "${BASE_IMAGE_PATH}" "${ALMA_IMAGE_URL}"
    qemu-img info "${BASE_IMAGE_PATH}" >/dev/null || fail "Image téléchargée invalide"
    ok "Image téléchargée"
fi

# -------------------------- Création des VMs --------------------------
SSH_PUBKEY_VALUE="$(cat "${SSH_PUBKEY_FILE}")"

for entry in "${VMS[@]}"; do
    IFS='|' read -r NAME IP MAC RAM CPU DISK TPL <<< "${entry}"

    log "=== ${NAME} (${IP}, MAC ${MAC}, ${RAM} MiB RAM, ${CPU} vCPU, ${DISK} GiB) ==="

    if virsh dominfo "${NAME}" >/dev/null 2>&1; then
        STATE=$(virsh domstate "${NAME}" 2>/dev/null || echo "")
        if [[ "${STATE}" == "running" ]]; then
            ok "${NAME} déjà en cours d'exécution"
            continue
        fi
        log "Démarrage de ${NAME} existante..."
        virsh start "${NAME}"
        continue
    fi

    DISK_PATH="${IMAGES_DIR}/${NAME}.qcow2"
    SEED_DIR="${CLOUD_INIT_DIR}/${NAME}"
    SEED_ISO="${SEED_DIR}/seed.iso"

    mkdir -p "${SEED_DIR}"

    # Génération user-data depuis template
    sed -e "s|__HOSTNAME__|${NAME}|g" \
        -e "s|__SSH_PUBKEY__|${SSH_PUBKEY_VALUE}|g" \
        "${CLOUD_INIT_DIR}/${TPL}.user-data.tmpl" > "${SEED_DIR}/user-data"

    # meta-data minimal — pas de network-config : l'IP est servie par
    # le bail DHCP statique du réseau libvirt (cf. <host> dans net-define).
    # AlmaLinux 10 utilise NetworkManager qui consomme directement le bail
    # DHCP, sans avoir à traduire un network-config Netplan.
    cat > "${SEED_DIR}/meta-data" <<EOF
instance-id: ${NAME}-$(date +%s)
local-hostname: ${NAME}
EOF

    # ISO seed cloud-init (user-data + meta-data, pas de network-config)
    cloud-localds -v \
        "${SEED_ISO}" \
        "${SEED_DIR}/user-data" \
        "${SEED_DIR}/meta-data"

    # Disque QCOW2 avec backing file
    log "Création du disque ${DISK_PATH}..."
    sudo qemu-img create -f qcow2 \
        -b "${BASE_IMAGE_PATH}" \
        -F qcow2 \
        "${DISK_PATH}" \
        "${DISK}G"

    # Création VM avec virt-install. La MAC est fixée pour matcher
    # le bail DHCP statique du réseau libvirt — la VM reçoit donc
    # directement l'IP de l'inventaire au DHCP, sans besoin de
    # network-config dans cloud-init.
    log "Création de la VM ${NAME}..."
    sudo virt-install \
        --name "${NAME}" \
        --memory "${RAM}" \
        --vcpus "${CPU}" \
        --disk "path=${DISK_PATH},format=qcow2" \
        --disk "path=${SEED_ISO},device=cdrom" \
        --os-variant almalinux10 \
        --network "network=${NETWORK_NAME},mac=${MAC}" \
        --graphics none \
        --console pty,target_type=serial \
        --noautoconsole \
        --import

    ok "VM ${NAME} créée"
done

echo ""
log "Attente du démarrage initial des VMs (60s)..."
sleep 60

log "État des VMs :"
for entry in "${VMS[@]}"; do
    NAME="${entry%%|*}"
    STATE=$(virsh domstate "${NAME}" 2>/dev/null || echo "inconnu")
    echo "  ${NAME}: ${STATE}"
done

echo ""
ok "Provisionnement terminé. Lance maintenant 'make verify-conn' pour valider Ansible."

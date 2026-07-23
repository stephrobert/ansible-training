#!/usr/bin/env bash
# Gère les entrées /etc/hosts du lab Ansible (côté poste apprenant).
#
# Usage :
#   scripts/manage-hosts.sh add      # ajoute les 4 hôtes du lab
#   scripts/manage-hosts.sh remove   # retire le bloc
#   scripts/manage-hosts.sh status   # affiche l'état
#
# Idempotent. Le bloc est délimité par des marqueurs pour permettre une
# suppression propre via `remove`.

set -euo pipefail

ACTION="${1:-status}"
HOSTS_FILE=/etc/hosts
MARKER_BEGIN="# BEGIN ansible-training lab-hosts"
MARKER_END="# END ansible-training lab-hosts"

# Les IP ne sont PAS codées ici : elles viennent du ssh_config que dsoxlab
# génère depuis les outputs Terraform, seule source de vérité.
#
# Ce script figeait 10.10.20.10/.21/.22/.31, « alignées sur les baux DHCP fixes »
# du temps de l ancien provision.sh. Terraform attribue désormais les adresses,
# et les quatre étaient fausses : web1.lab pointait .21 pour une machine en .12.
# Le poste est le noeud de contrôle : tout ce qui résout un nom de lab depuis
# ici tombait à côté.
SSH_CONFIG="${XDG_CACHE_HOME:-$HOME/.cache}/dsoxlab/ansible-training/ssh_config"

if [ ! -f "$SSH_CONFIG" ]; then
    echo "ssh_config dsoxlab introuvable : $SSH_CONFIG" >&2
    echo "L infrastructure est-elle provisionnée ? Lance 'mise run provision'." >&2
    exit 1
fi

# `Host <nom>` puis `HostName <ip>` : on apparie les deux.
ENTRIES=$(awk '
    /^Host / { nom = $2 }
    /^[[:space:]]*HostName / && nom { print $2, nom; nom = "" }
' "$SSH_CONFIG")

if [ -z "$ENTRIES" ]; then
    echo "Aucun hôte dans $SSH_CONFIG : rien à publier." >&2
    exit 1
fi

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

block_present() {
    grep -qF "$MARKER_BEGIN" "$HOSTS_FILE" 2>/dev/null
}

case "$ACTION" in
    add)
        if block_present; then
            echo -e "${YELLOW}[skip]${NC} Bloc lab déjà présent dans ${HOSTS_FILE}."
            echo "       Lance '$0 status' pour voir, '$0 remove' puis '$0 add' pour resynchroniser."
            exit 0
        fi
        echo -e "${BLUE}[hosts]${NC} Ajout des 4 hôtes du lab dans ${HOSTS_FILE} (sudo nécessaire)..."
        sudo tee -a "$HOSTS_FILE" >/dev/null <<EOF

${MARKER_BEGIN}
${ENTRIES}
${MARKER_END}
EOF
        echo -e "${GREEN}[OK]${NC} Bloc ajouté. Tu peux maintenant 'ssh student@web1.lab', etc."
        ;;

    remove)
        if ! block_present; then
            echo -e "${YELLOW}[skip]${NC} Bloc lab absent de ${HOSTS_FILE} — rien à faire."
            exit 0
        fi
        echo -e "${BLUE}[hosts]${NC} Retrait du bloc lab de ${HOSTS_FILE} (sudo nécessaire)..."
        sudo sed -i "/${MARKER_BEGIN}/,/${MARKER_END}/d" "$HOSTS_FILE"
        # Compresse les lignes vides consécutives qui pourraient rester
        sudo sed -i '/./,/^$/!d' "$HOSTS_FILE"
        echo -e "${GREEN}[OK]${NC} Bloc retiré."
        ;;

    status)
        if block_present; then
            echo -e "${GREEN}[OK]${NC} Bloc lab présent dans ${HOSTS_FILE} :"
            sed -n "/${MARKER_BEGIN}/,/${MARKER_END}/p" "$HOSTS_FILE" | sed 's/^/  /'
        else
            echo -e "${YELLOW}[ko]${NC} Bloc lab absent de ${HOSTS_FILE}."
            echo "      Lance '$0 add' pour pouvoir résoudre web1.lab, web2.lab, db1.lab, control-node.lab."
        fi
        ;;

    *)
        echo "Usage : $0 {add|remove|status}" >&2
        exit 1
        ;;
esac

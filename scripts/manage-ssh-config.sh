#!/usr/bin/env bash
# Gère le fragment ~/.ssh/config.d/ansible-training.conf qui mappe les hôtes
# du lab (web1.lab, web2.lab, db1.lab, control-node.lab + leurs IPs) sur la
# clé SSH dédiée du repo (ssh/id_ed25519).
#
# Usage :
#   scripts/manage-ssh-config.sh add      # crée le fragment
#   scripts/manage-ssh-config.sh remove   # supprime le fragment
#   scripts/manage-ssh-config.sh status   # affiche l'état
#
# Idempotent. Le fragment est un fichier dédié pour permettre une suppression
# propre via `remove` (rm), pas une édition de ~/.ssh/config.

set -euo pipefail

ACTION="${1:-status}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSH_CONF_DIR="${HOME}/.ssh/config.d"
FRAGMENT="${SSH_CONF_DIR}/ansible-training.conf"
MAIN_CONF="${HOME}/.ssh/config"
LAB_KEY="${REPO_ROOT}/ssh/id_ed25519"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

case "$ACTION" in
    add)
        if [ ! -f "$LAB_KEY" ]; then
            echo -e "${RED}[err]${NC} Clé du lab introuvable : ${LAB_KEY}"
            echo "      Lance 'make bootstrap' à la racine du repo pour la générer."
            exit 1
        fi
        mkdir -p "$SSH_CONF_DIR"
        chmod 700 "$SSH_CONF_DIR"
        if ! grep -qE '^\s*Include\s+(~/\.ssh/)?config\.d/' "$MAIN_CONF" 2>/dev/null; then
            echo -e "${YELLOW}[warn]${NC} ${MAIN_CONF} n'inclut pas ~/.ssh/config.d/*.conf."
            echo "       Ajoute en première ligne de ${MAIN_CONF} :"
            echo "         Include ~/.ssh/config.d/*.conf"
            echo "       Sinon le fragment sera créé mais ssh ne le lira pas."
        fi
        if [ -f "${SSH_CONF_DIR}/lab-ansible.conf" ]; then
            echo -e "${YELLOW}[warn]${NC} ${SSH_CONF_DIR}/lab-ansible.conf existe (ancienne config)."
            echo "       Si tu n'utilises plus l'ancien repo lab-ansible, supprime-le :"
            echo "         rm ${SSH_CONF_DIR}/lab-ansible.conf"
        fi
        echo -e "${BLUE}[ssh]${NC} Création de ${FRAGMENT}..."
        cat > "$FRAGMENT" <<EOF
# BEGIN ansible-training lab-ssh
# Généré par scripts/manage-ssh-config.sh — édition manuelle écrasée à chaque 'add'.
# Mappe les 4 hôtes du lab (hostnames + IPs) sur la clé SSH dédiée du repo.
Host web1.lab web2.lab db1.lab control-node.lab 10.10.20.10 10.10.20.21 10.10.20.22 10.10.20.31
    User ansible
    IdentityFile ${LAB_KEY}
    IdentitiesOnly yes
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
    ProxyJump none
    ProxyCommand none
# END ansible-training lab-ssh
EOF
        chmod 600 "$FRAGMENT"
        echo -e "${GREEN}[OK]${NC} Fragment créé. 'ssh ansible@web1.lab' devrait fonctionner."
        ;;

    remove)
        if [ ! -f "$FRAGMENT" ]; then
            echo -e "${YELLOW}[skip]${NC} ${FRAGMENT} absent — rien à faire."
            exit 0
        fi
        rm -f "$FRAGMENT"
        echo -e "${GREEN}[OK]${NC} ${FRAGMENT} supprimé."
        ;;

    status)
        if [ -f "$FRAGMENT" ]; then
            echo -e "${GREEN}[OK]${NC} Fragment présent : ${FRAGMENT}"
            sed -n '1,20p' "$FRAGMENT" | sed 's/^/  /'
            if ! grep -qE '^\s*Include\s+(~/\.ssh/)?config\.d/' "$MAIN_CONF" 2>/dev/null; then
                echo ""
                echo -e "${YELLOW}[warn]${NC} ${MAIN_CONF} n'inclut pas ~/.ssh/config.d/*.conf — le fragment ne sera pas lu."
            fi
        else
            echo -e "${YELLOW}[ko]${NC} Fragment absent : ${FRAGMENT}"
            echo "      Lance '$0 add' pour le créer."
        fi
        ;;

    *)
        echo "Usage : $0 {add|remove|status}" >&2
        exit 1
        ;;
esac

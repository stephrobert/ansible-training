#!/usr/bin/env bash
# Installe les outils requis pour le lab Ansible RHCE.
#
# Stratégie d'installation alignée sur la pratique de la machine hôte :
# - mise gère ansible (déjà installé), python, ansible-lint
# - pipx gère les outils Python isolés (ansible-navigator, molecule, yamllint)
# - dnf gère les paquets système (libvirt, qemu, virt-install, cloud-localds)
#
# La roadmap §12.7 propose pip --user ; on le remplace par mise/pipx pour rester
# cohérent avec l'environnement de l'auteur (cf. mémoire feedback).

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log()    { echo -e "\033[0;34m[bootstrap]\033[0m $*"; }
ok()     { echo -e "\033[0;32m[OK]\033[0m $*"; }
warn()   { echo -e "\033[0;33m[WARN]\033[0m $*"; }
fail()   { echo -e "\033[0;31m[FAIL]\033[0m $*" >&2; exit 1; }

# ---------------------------------------------------------------------
# 1. Paquets système (libvirt + virt-install + cloud-localds)
# ---------------------------------------------------------------------
log "Vérification des paquets système..."

PKG_MGR=""
if command -v dnf >/dev/null 2>&1; then PKG_MGR=dnf
elif command -v apt-get >/dev/null 2>&1; then PKG_MGR=apt
fi

case "${PKG_MGR}" in
  dnf)
    SYS_PACKAGES=(libvirt qemu-kvm virt-install cloud-utils libguestfs-tools openssh-clients make git)
    for pkg in "${SYS_PACKAGES[@]}"; do
      rpm -q "${pkg}" >/dev/null 2>&1 || { log "Installation: ${pkg}"; sudo dnf install -y "${pkg}"; }
    done
    ;;
  apt)
    SYS_PACKAGES=(libvirt-daemon-system libvirt-clients qemu-kvm virtinst cloud-image-utils libguestfs-tools openssh-client make git)
    sudo apt-get update -qq
    for pkg in "${SYS_PACKAGES[@]}"; do
      dpkg -l "${pkg}" >/dev/null 2>&1 || { log "Installation: ${pkg}"; sudo apt-get install -y "${pkg}"; }
    done
    ;;
  *)
    warn "Gestionnaire de paquets non détecté — vérifie manuellement la présence de virt-install, cloud-localds, libvirt"
    ;;
esac

ok "Paquets système OK"

# ---------------------------------------------------------------------
# 2. libvirt actif
# ---------------------------------------------------------------------
log "Vérification de libvirtd..."
sudo systemctl enable --now libvirtd >/dev/null 2>&1 || true
systemctl is-active --quiet libvirtd && ok "libvirtd actif" || fail "libvirtd ne démarre pas"

# ---------------------------------------------------------------------
# 3. Outils Python via mise + pipx
# ---------------------------------------------------------------------
log "Vérification des outils Ansible via mise/pipx..."

if ! command -v mise >/dev/null 2>&1; then
    fail "mise n'est pas installé sur ce poste — voir https://mise.jdx.dev/getting-started.html"
fi

# ansible-core est typiquement déjà installé via mise (cf. mise list)
if ! mise which ansible >/dev/null 2>&1 && ! command -v ansible >/dev/null 2>&1; then
    log "Installation d'ansible via mise..."
    mise use -g ansible@latest
fi
ok "ansible présent : $(ansible --version | head -1)"

# ansible-lint via pipx (déjà géré par mise pipx:ansible-lint sur le poste)
if ! command -v ansible-lint >/dev/null 2>&1; then
    log "Installation d'ansible-lint via pipx..."
    pipx install ansible-lint
fi
ok "ansible-lint présent : $(ansible-lint --version | head -1)"

# ansible-navigator via pipx (RHCE EX294 — outil obligatoire)
if ! command -v ansible-navigator >/dev/null 2>&1; then
    log "Installation d'ansible-navigator via pipx..."
    pipx install ansible-navigator
fi
ok "ansible-navigator présent : $(ansible-navigator --version 2>/dev/null | head -1 || echo 'installé')"

# molecule via pipx
if ! command -v molecule >/dev/null 2>&1; then
    log "Installation de molecule via pipx..."
    pipx install --include-deps molecule
    pipx inject molecule "molecule-plugins[docker,libvirt]" || warn "molecule-plugins[libvirt] non installé — installer manuellement si besoin"
fi
ok "molecule présent : $(molecule --version | head -1)"

# yamllint via pipx
if ! command -v yamllint >/dev/null 2>&1; then
    log "Installation de yamllint via pipx..."
    pipx install yamllint
fi
ok "yamllint présent : $(yamllint --version)"

# pytest + pytest-testinfra (pour valider les challenges des labs unitaires)
if ! command -v pytest >/dev/null 2>&1; then
    log "Installation de pytest via pipx..."
    pipx install pytest
fi
# pytest-testinfra doit être injecté dans le venv pytest (idempotent)
if ! pipx runpip pytest list 2>/dev/null | grep -qi testinfra; then
    log "Injection de pytest-testinfra dans pytest..."
    pipx inject pytest pytest-testinfra
fi
ok "pytest présent : $(pytest --version) + testinfra"

# ---------------------------------------------------------------------
# 4. Collections Galaxy
# ---------------------------------------------------------------------
log "Installation des collections Galaxy depuis requirements.yml..."
ansible-galaxy collection install -r "${LAB_DIR}/requirements.yml" --upgrade 2>&1 | tail -10 || warn "Certaines collections n'ont pas pu être installées"
ok "Collections Galaxy installées"

# ---------------------------------------------------------------------
# 5. Clé SSH du lab
# ---------------------------------------------------------------------
SSH_KEY="${LAB_DIR}/ssh/id_ed25519"
if [[ ! -f "${SSH_KEY}" ]]; then
    log "Génération de la clé SSH du lab (ssh/id_ed25519)..."
    ssh-keygen -t ed25519 -N "" -f "${SSH_KEY}" -C "ansible-lab@$(hostname)" >/dev/null
    chmod 600 "${SSH_KEY}"
    ok "Clé SSH créée : ${SSH_KEY}"
else
    ok "Clé SSH existante conservée : ${SSH_KEY}"
fi

# ---------------------------------------------------------------------
# 6. Récap
# ---------------------------------------------------------------------
echo ""
ok "Bootstrap terminé."
echo ""
log "Prochaine étape : make provision"

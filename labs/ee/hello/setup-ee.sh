#!/usr/bin/env bash
# setup-ee.sh — installe Podman + ansible-navigator pour le lab EE.
# Cible : poste de dev (laptop ou control-node).
# Compatible : Fedora 40+, AlmaLinux/RHEL 9+/10, Ubuntu 24.04+.
set -euo pipefail

echo "[setup-ee] Vérification Podman..."
if command -v podman >/dev/null 2>&1; then
  echo "  → podman $(podman --version | awk '{print $3}') OK"
else
  echo "  → Podman absent. Installation requise :"
  if [ -f /etc/almalinux-release ] || [ -f /etc/redhat-release ]; then
    echo "    sudo dnf install -y podman"
  elif [ -f /etc/lsb-release ]; then
    echo "    sudo apt-get update && sudo apt-get install -y podman"
  fi
  exit 1
fi

echo "[setup-ee] Vérification ansible-navigator..."
if command -v ansible-navigator >/dev/null 2>&1; then
  echo "  → ansible-navigator $(ansible-navigator --version | awk '{print $2}') OK"
else
  echo "  → ansible-navigator absent. Installation recommandée :"
  echo "    pipx install ansible-navigator"
  exit 1
fi

echo "[setup-ee] Pull de l'EE community creator-ee..."
podman pull quay.io/ansible/creator-ee:latest || \
  echo "  → pull échoué (réseau / proxy ?), check 'podman info' "

echo "[setup-ee] OK — environnement prêt pour le lab 84."
echo ""
echo "Étape suivante :"
echo "  ansible-navigator run ping.yml -i inventory.yml --eei quay.io/ansible/creator-ee:latest -m stdout"

#!/usr/bin/env bash
# inspect.sh — utilise ansible-navigator images pour inspecter 3 EE.
# Affiche : ansible-core version, collections embarquées, Python deps,
# system deps, taille des images.
set -euo pipefail

EE_LIST=(
  "quay.io/ansible/creator-ee:latest"
  "quay.io/ansible/awx-ee:latest"
  "quay.io/ansible/community-ee-minimal:latest"
)

echo "[inspect] Pull des 3 EE pour comparaison..."
for ee in "${EE_LIST[@]}"; do
  podman pull "$ee" || echo "  ⚠ pull KO pour $ee"
done

echo ""
echo "[inspect] Tailles comparées :"
podman images | awk 'NR==1 || /ee/' | head -10

echo ""
echo "[inspect] Collections embarquées dans creator-ee :"
podman run --rm "${EE_LIST[0]}" ansible-galaxy collection list 2>&1 | head -30

echo ""
echo "[inspect] Version ansible-core par EE :"
for ee in "${EE_LIST[@]}"; do
  printf "  %s : " "$ee"
  podman run --rm "$ee" ansible --version 2>/dev/null | head -1 || echo "(KO)"
done

echo ""
echo "[inspect] Pour exploration interactive :"
echo "  ansible-navigator images --eei ${EE_LIST[0]}"
echo "  ansible-navigator doc ansible.builtin.copy --eei ${EE_LIST[0]}"

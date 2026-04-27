#!/usr/bin/env bash
# build-ee.sh — build l'EE custom du lab 86 avec ansible-builder v3.
set -euo pipefail

EE_TAG="${EE_TAG:-localhost/lab86-my-ee:1.0.0}"

if ! command -v ansible-builder >/dev/null 2>&1; then
  echo "[build-ee] ansible-builder absent."
  echo "  → pipx install ansible-builder"
  exit 1
fi

echo "[build-ee] Build $EE_TAG via Podman..."
ansible-builder build \
  --tag "$EE_TAG" \
  --container-runtime podman \
  --file execution-environment.yml \
  --context ./context \
  --verbosity 2

echo ""
echo "[build-ee] OK — image disponible :"
podman images | grep "lab86" || true

echo ""
echo "[build-ee] Test rapide :"
echo "  podman run --rm $EE_TAG ansible --version | head -1"
echo "  podman run --rm $EE_TAG ansible-galaxy collection list"

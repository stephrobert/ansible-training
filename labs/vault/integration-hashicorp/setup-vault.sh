#!/usr/bin/env bash
# setup-vault.sh — démarre HashiCorp Vault en mode dev local pour le lab.
# Compatible avec OpenBao : remplacer 'hashicorp/vault' par 'openbao/openbao'.
set -euo pipefail

CONTAINER_NAME="${CONTAINER_NAME:-vault-lab82}"
VAULT_TOKEN="${VAULT_TOKEN:-lab82-root}"
VAULT_PORT="${VAULT_PORT:-8200}"
IMAGE="${IMAGE:-hashicorp/vault:latest}"

echo "[setup-vault] Lancement de $IMAGE..."
podman run -d --rm \
  --name="$CONTAINER_NAME" \
  -p "${VAULT_PORT}:8200" \
  -e "VAULT_DEV_ROOT_TOKEN_ID=$VAULT_TOKEN" \
  -e "VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200" \
  --cap-add=IPC_LOCK \
  "$IMAGE" || echo "(container peut-être déjà lancé)"

sleep 3

echo "[setup-vault] Test de connectivité..."
export VAULT_ADDR="http://localhost:${VAULT_PORT}"
export VAULT_TOKEN

# Pose les secrets de démo dans le KV v2
podman exec -e VAULT_TOKEN -e VAULT_ADDR=http://0.0.0.0:8200 \
  "$CONTAINER_NAME" \
  vault kv put secret/lab82 \
    db_password=VaultPassLab82 \
    api_key=vault_api_xyz_lab82

echo "[setup-vault] OK — Vault disponible sur $VAULT_ADDR"
echo "  Token : $VAULT_TOKEN"
echo "  Path  : secret/lab82"
echo ""
echo "Variables d'env à exporter pour le playbook :"
echo "  export VAULT_ADDR=$VAULT_ADDR"
echo "  export VAULT_TOKEN=$VAULT_TOKEN"

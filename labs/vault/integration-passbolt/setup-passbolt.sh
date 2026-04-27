#!/usr/bin/env bash
# setup-passbolt.sh — démarre Passbolt CE en local via Podman pour le lab.
# Passbolt = gestionnaire de mots de passe d'équipe basé sur OpenPGP.
# Architecture : MariaDB + Passbolt API (PHP) + UI web.
set -euo pipefail

NETWORK="${NETWORK:-passbolt-lab83}"
DB_CONTAINER="${DB_CONTAINER:-passbolt-db-lab83}"
APP_CONTAINER="${APP_CONTAINER:-passbolt-app-lab83}"
PASSBOLT_PORT="${PASSBOLT_PORT:-8443}"

echo "[setup-passbolt] Création du réseau $NETWORK..."
podman network create "$NETWORK" 2>/dev/null || echo "(network déjà présent)"

echo "[setup-passbolt] Démarrage MariaDB..."
podman run -d --rm \
  --name="$DB_CONTAINER" \
  --network="$NETWORK" \
  -e MYSQL_ROOT_PASSWORD=rootlab83 \
  -e MYSQL_DATABASE=passbolt \
  -e MYSQL_USER=passbolt \
  -e MYSQL_PASSWORD=passboltlab83 \
  docker.io/library/mariadb:11 \
  || echo "(db container peut-être déjà lancé)"

sleep 6

echo "[setup-passbolt] Démarrage Passbolt CE..."
podman run -d --rm \
  --name="$APP_CONTAINER" \
  --network="$NETWORK" \
  -p "${PASSBOLT_PORT}:443" \
  -e APP_FULL_BASE_URL="https://localhost:${PASSBOLT_PORT}" \
  -e DATASOURCES_DEFAULT_HOST="$DB_CONTAINER" \
  -e DATASOURCES_DEFAULT_USERNAME=passbolt \
  -e DATASOURCES_DEFAULT_PASSWORD=passboltlab83 \
  -e DATASOURCES_DEFAULT_DATABASE=passbolt \
  docker.io/passbolt/passbolt:latest-ce \
  || echo "(app container peut-être déjà lancé)"

sleep 10

echo "[setup-passbolt] Initialisation admin user..."
podman exec "$APP_CONTAINER" su -m -c \
  "/usr/share/php/passbolt/bin/cake passbolt register_user \
    -u admin@lab83.local \
    -f Lab83 -l Admin \
    -r admin" www-data \
  || echo "(admin déjà créé)"

echo ""
echo "[setup-passbolt] OK — Passbolt disponible sur https://localhost:${PASSBOLT_PORT}"
echo ""
echo "Étapes suivantes (manuelles via UI) :"
echo "  1. Ouvrir https://localhost:${PASSBOLT_PORT} (accepter le certif self-signed)"
echo "  2. Compléter l'inscription via le lien retourné par 'register_user'"
echo "  3. Générer/uploader une clé OpenPGP pour l'utilisateur Ansible"
echo "  4. Exporter la clé privée dans .passbolt/private.key (mode 0600)"
echo ""
echo "Variables pour le playbook :"
echo "  export PASSBOLT_URL=https://localhost:${PASSBOLT_PORT}"
echo "  export PASSBOLT_PRIVATE_KEY=\$(cat .passbolt/private.key)"
echo "  export PASSBOLT_PASSPHRASE='votre-passphrase'"

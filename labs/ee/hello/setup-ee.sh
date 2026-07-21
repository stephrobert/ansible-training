#!/usr/bin/env bash
# setup-ee.sh : À COMPLÉTER PAR VOS SOINS.
#
# Ce script doit préparer le poste pour le lab :
#   1. vérifier que podman est présent (sinon guider l'installation),
#   2. vérifier qu'ansible-navigator est présent (sinon guider pipx),
#   3. pré-tirer l'image EE officielle creator-ee.
set -euo pipefail

command -v ??? >/dev/null 2>&1 || { echo "installez ???"; exit 1; }

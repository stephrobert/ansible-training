#!/usr/bin/env bash
# inspect.sh : À COMPLÉTER PAR VOS SOINS.
#
# Ce script doit inspecter et comparer 3 EE officiels :
#   - community-ansible-dev-tools, awx-ee, community-ee-minimal.
# Pour chacun : version d'ansible-core, collections embarquées, taille
# d'image. Il doit aussi générer le rapport
# inspect-output/comparison.md (tableau Markdown de la comparaison).
#
# Outils attendus : podman (pull, run, image inspect) et
# ansible-navigator (exploration structurée).
set -euo pipefail

EE_LIST=(
  "???"
)

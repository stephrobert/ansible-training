#!/usr/bin/env bash
# Joue les tests de tous les labs contre l'infrastructure provisionnée.
#
# Avant la migration dsoxlab, ce script bouclait `make setup run verify clean`
# dans chaque répertoire de lab. Il était déjà cassé : 2 labs seulement avaient
# une cible `setup`, 4 une cible `verify`. Les Makefile par lab n'existent plus
# (le validator dsoxlab les interdit) et les tests sont des tests
# pytest+testinfra : on les lance directement.
#
# Pour UN lab, préférer la CLI, qui pose l'état de départ et désactive le rejeu
# de la solution :
#     dsoxlab check <id-du-lab>
#
# Ce script sert au formateur : il rejoue TOUT. La fixture _apply_lab_state du
# conftest applique alors la solution de référence de chaque lab avant ses
# tests : c'est le contrôle « mes solutions passent mes propres tests ».
# Il exige les 4 VMs joignables et .vault-pass présent.

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${LAB_DIR}"

log()  { echo -e "\033[0;34m[test-all]\033[0m $*"; }
ok()   { echo -e "\033[0;32m[OK]\033[0m $*"; }
fail() { echo -e "\033[0;31m[FAIL]\033[0m $*" >&2; }

if [[ ! -d labs ]]; then
    fail "labs/ introuvable — à lancer depuis la racine du dépôt."
    exit 1
fi

# Un catalogue vide doit ÉCHOUER, pas passer en silence : c'était le piège de
# la version précédente, qui sortait verte dès qu'elle ne trouvait aucun
# Makefile — donc systématiquement une fois ceux-ci supprimés.
lab_count="$(find labs -mindepth 2 -maxdepth 2 -type d | wc -l)"
if [[ "${lab_count}" -eq 0 ]]; then
    fail "aucun lab trouvé sous labs/ : catalogue vide ?"
    exit 1
fi
log "${lab_count} labs — tests joués avec la solution de référence"

if [[ ! -f .vault-pass ]]; then
    fail ".vault-pass absent : les solutions chiffrées ne peuvent pas être rejouées."
    exit 1
fi

if pytest labs/ "$@"; then
    ok "tous les labs passent"
else
    fail "au moins un lab échoue (voir ci-dessus)"
    exit 1
fi

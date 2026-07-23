#!/usr/bin/env bash
# Refige l'état de base des VM pour l'isolation RAPIDE des labs.
#
# C'EST L'OPÉRATION À LANCER APRÈS TOUT `dsoxlab provision`.
#
# Pourquoi elle est obligatoire : provision recrée les domaines libvirt, et
# Terraform leur attribue un UUID neuf. Or libvirt REFUSE de restaurer un état
# mémoire vers un domaine dont l'UUID diffère, alors que le NOM, lui, n'a pas
# bougé. Les `.mem.save` d'avant le provision sont donc morts sans que rien ne
# le signale : chaque lab tentait un restore voué à l'échec, laissait sa VM
# éteinte, puis attendait 240 s par hôte. Sur 113 labs, la suite paraissait
# figée. Le conftest détecte désormais ce cas et retombe sur un boot complet,
# mais le boot complet coûte des heures sur le catalogue entier : rebaser reste
# la bonne réponse.
#
# À NE PAS CONFONDRE avec `mise run snapshot`, qui pose des snapshots libvirt
# internes (refusés sur nos domaines UEFI/pflash) et ne prépare RIEN pour
# l'isolation des labs.
set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${LAB_DIR}"

log() { echo -e "\033[0;34m[rebase]\033[0m $*"; }
ok()  { echo -e "\033[0;32m[OK]\033[0m $*"; }

log "Basing des VM du meta.yml : boot complet puis gel mémoire, comptez quelques minutes."

python3 - <<'PY'
import sys
sys.path.insert(0, ".")
import conftest as c

fqdns = c._meta_vm_fqdns()
if not fqdns:
    sys.exit("meta.yml ne déclare aucun hôte : rien à rebaser.")
print(f"  hôtes : {', '.join(fqdns)}")
c.snapshot_base(fqdns)

# Vérifie ce qu'on vient d'écrire plutôt que de l'annoncer : un golden dont
# l'UUID ne correspond pas au domaine est exactement le défaut qu'on répare.
mauvais = [f for f in fqdns if not c._golden_is_usable(f, c._mem_save_path(f))]
if mauvais:
    sys.exit(f"golden toujours périmé pour : {', '.join(mauvais)}")
print("  golden vérifiés : UUID cohérents avec les domaines")
PY

ok "VM rebasées : le reset par lab repart en mode rapide."

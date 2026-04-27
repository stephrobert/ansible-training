#!/usr/bin/env bash
# prep-environment.sh — pose un environnement "examen propre" sur les 4 VMs.
#
# Conçu pour que l'apprenant qui démarre le mock RHCE EX294 ne perde pas 30 min
# en troubleshooting d'état hérité d'autres labs. Idempotent.
#
# Actions :
#   1. db1.lab : provisionne le VG `vg_lab` (image loop 400 Mo) — pré-requis T10.
#   2. Tous : libère l'UID 2001 (supprime les users squattant) — pré-requis T7.
#   3. webservers : arrête + désinstalle nginx s'il occupe le port 80 — pré-requis T5/T6.
#
# Usage :
#   cd /home/bob/Projets/ansible-training
#   labs/rhce/mock-ex294/prep-environment.sh
#
# Lancer ce script AVANT de démarrer le chrono.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

echo "════════════════════════════════════════════════════════════════"
echo "  Préparation de l'environnement Mock RHCE EX294"
echo "════════════════════════════════════════════════════════════════"

# ─── 1) VG `vg_lab` sur db1.lab ───────────────────────────────────────────
echo
echo "▶ [1/3] Provisionnement du VG 'vg_lab' sur db1.lab (pré-requis T10)…"

ansible db1.lab -b -m ansible.builtin.shell -a "
set -e
if vgs vg_lab >/dev/null 2>&1; then
    echo 'vg_lab déjà présent — skip.'
    exit 0
fi
# Si état pathologique (/dev/vg_lab survit après vgremove partiel), tout réinitialiser
umount /mnt/data 2>/dev/null || true
sed -i '/\\/mnt\\/data/d' /etc/fstab
test -e /dev/vg_lab/lv_data && lvchange -an /dev/vg_lab/lv_data 2>/dev/null || true
test -d /dev/vg_lab && dmsetup remove_all 2>/dev/null || true
losetup -D 2>/dev/null || true
test -f /opt/lab100-disk.img || dd if=/dev/zero of=/opt/lab100-disk.img bs=1M count=400 status=none
losetup -f /opt/lab100-disk.img
LOOP=\$(losetup -j /opt/lab100-disk.img | cut -d: -f1 | head -1)
pvcreate -ff -y \$LOOP >/dev/null
vgcreate vg_lab \$LOOP >/dev/null
echo \"vg_lab créé sur \$LOOP\"
" 2>&1 | tail -5

# ─── 2) Libérer UID 2001 sur tous les hôtes ───────────────────────────────
echo
echo "▶ [2/3] Libération de l'UID 2001 (pré-requis T7)…"

ansible all -b -m ansible.builtin.shell -a "
set -e
SQUATTER=\$(getent passwd 2001 | cut -d: -f1)
if [ -n \"\$SQUATTER\" ] && [ \"\$SQUATTER\" != 'appuser' ]; then
    userdel -r \"\$SQUATTER\" 2>/dev/null || true
    echo \"User \$SQUATTER (UID 2001) supprimé.\"
fi
SQUATTER_GRP=\$(getent group 2001 | cut -d: -f1)
if [ -n \"\$SQUATTER_GRP\" ] && [ \"\$SQUATTER_GRP\" != 'appgroup' ]; then
    groupdel \"\$SQUATTER_GRP\" 2>/dev/null || true
    echo \"Group \$SQUATTER_GRP (GID 2001) supprimé.\"
fi
true
" 2>&1 | tail -8

# ─── 3) Libérer port 80 sur webservers ────────────────────────────────────
echo
echo "▶ [3/3] Libération du port 80 sur webservers (pré-requis T5/T6)…"

ansible webservers -b -m ansible.builtin.shell -a "
set -e
if rpm -q nginx >/dev/null 2>&1; then
    systemctl stop nginx 2>/dev/null || true
    systemctl disable nginx 2>/dev/null || true
    dnf -y -q remove nginx >/dev/null
    echo 'nginx désinstallé.'
fi
# httpd peut tourner avec un Listen non-80 — restaurer le défaut
if rpm -q httpd >/dev/null 2>&1 && grep -q '^Listen ' /etc/httpd/conf/httpd.conf; then
    sed -i 's/^Listen .*/Listen 80/' /etc/httpd/conf/httpd.conf
fi
true
" 2>&1 | tail -5

echo
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ Environnement prêt. Démarrez le chrono."
echo "════════════════════════════════════════════════════════════════"
echo
echo "Lancement attendu :"
echo
echo "  ANSIBLE_ROLES_PATH=labs/rhce/mock-ex294/roles \\"
echo "  ansible-playbook \\"
echo "    -i labs/rhce/mock-ex294/inventory/hosts.yml \\"
echo "    --vault-password-file labs/rhce/mock-ex294/.vault_password \\"
echo "    labs/rhce/mock-ex294/challenge/solution.yml"
echo
echo "Validation :"
echo "  pytest -v labs/rhce/mock-ex294/challenge/tests/"

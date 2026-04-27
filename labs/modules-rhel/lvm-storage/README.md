# Lab 48 — LVM storage : `lvg:` + `lvol:` + `filesystem:` + `mount:`

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `make bootstrap && make provision` à la racine du repo (cf.
> [README racine](../../README.md#-démarrage-rapide) pour les détails).

## 🧠 Rappel

🔗 [**LVM avec Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/rhel-systeme/lvm-storage/)

LVM (Logical Volume Manager) abstrait les disques physiques en **volumes
logiques redimensionnables**. Pipeline classique :

1. **PV** (Physical Volume) — disque ou partition initialisée pour LVM.
2. **VG** (Volume Group) — pool de PVs combinés.
3. **LV** (Logical Volume) — volume découpé dans le VG (le "disque virtuel"
   utilisable).

Modules Ansible :

- **`community.general.lvg:`** — gérer les Volume Groups (créer/supprimer,
  ajouter des PVs).
- **`community.general.lvol:`** — gérer les Logical Volumes (créer, étendre,
  supprimer).
- **`community.general.filesystem:`** — formater un LV ou un disque.
- **`ansible.posix.mount:`** — monter et persister dans fstab (lab 47).

Sur RHCE 2026, ces 4 modules forment le **pipeline storage complet**.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Créer un loop device** pour simuler un disque sur n'importe quelle VM.
2. **Construire un PV → VG → LV** en chaîne avec les 3 modules dédiés.
3. **Formater** un LV en `xfs` ou `ext4` avec idempotence.
4. **Monter** le LV via `/dev/<vg>/<lv>` dans fstab.
5. **Étendre** un LV à chaud avec `lvol: resizefs: true`.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible-galaxy collection install community.general ansible.posix
ansible db1.lab -m ping

# Nettoyer un lab precedent
ansible db1.lab -b -m shell -a "umount /mnt/lvm-data 2>/dev/null; lvremove -f /dev/lab_vg/lab_lv 2>/dev/null; vgremove -f lab_vg 2>/dev/null; pvremove -f /dev/loop10 2>/dev/null; losetup -d /dev/loop10 2>/dev/null; rm -rf /opt/lab-lvm.img /mnt/lvm-data; sed -i '/lvm-data\\|lab_vg/d' /etc/fstab; true"
```

## 📚 Exercice 1 — Créer un loop device persistant

Pour simuler un disque dédié, on utilise un fichier image associé à un loop
device (`/dev/loop10`). Pour qu'il **persiste au reboot**, on configure
**`losetup`** au démarrage via `systemd`.

```yaml
---
- name: Setup loop device pour LVM
  hosts: db1.lab
  become: true
  tasks:
    - name: Creer fichier image 200M
      ansible.builtin.command:
        cmd: dd if=/dev/zero of=/opt/lab-lvm.img bs=1M count=200
        creates: /opt/lab-lvm.img

    - name: Associer au loop device 10 (idempotent)
      ansible.builtin.shell: |
        if ! losetup /dev/loop10 2>/dev/null; then
          losetup /dev/loop10 /opt/lab-lvm.img
          echo CHANGED
        fi
      register: loop_setup
      changed_when: "'CHANGED' in loop_setup.stdout"

    - name: Verifier
      ansible.builtin.command: losetup -l /dev/loop10
      register: loop_status
      changed_when: false

    - name: Afficher
      ansible.builtin.debug:
        var: loop_status.stdout_lines
```

🔍 **Observation** : `/dev/loop10` est maintenant un device bloc qui pointe sur
`/opt/lab-lvm.img` (200Mo). Visible dans `lsblk`.

**Limitation** : `losetup` n'est **pas persistant au reboot**. Pour un vrai lab
production, vous utiliseriez un **disque physique**. Pour ce lab, à chaque
reboot, il faut relancer le playbook (ou créer une unit systemd).

## 📚 Exercice 2 — Créer le PV + VG (`lvg:`)

```yaml
- name: Creer le Volume Group lab_vg sur loop10
  community.general.lvg:
    vg: lab_vg
    pvs: /dev/loop10
    state: present
```

🔍 **Observation** : le module fait **2 choses** :

1. **`pvcreate /dev/loop10`** — initialise le PV.
2. **`vgcreate lab_vg /dev/loop10`** — crée le VG sur ce PV.

**Idempotent** : 2e run → `changed=0`.

**Vérifier** :

```bash
ssh ansible@db1.lab 'sudo vgdisplay lab_vg | head -10'
ssh ansible@db1.lab 'sudo pvs'
```

**Étendre le VG** ultérieurement avec un nouveau disque :

```yaml
- community.general.lvg:
    vg: lab_vg
    pvs: /dev/loop10,/dev/loop11   # Ajout du 2e disque
    state: present
```

## 📚 Exercice 3 — Créer le LV (`lvol:`)

```yaml
- name: Creer le Logical Volume lab_lv (100M)
  community.general.lvol:
    vg: lab_vg
    lv: lab_lv
    size: 100M
    state: present
```

**Format de `size:`** :

- **`100M`** — taille fixe.
- **`50%FREE`** — 50% de l'espace libre du VG.
- **`+10G`** — extension de 10Go (relatif).

🔍 **Observation** : le LV est créé à `/dev/lab_vg/lab_lv` (ou
`/dev/mapper/lab_vg-lab_lv`). Visible dans `lsblk` :

```bash
ssh ansible@db1.lab 'sudo lsblk /dev/loop10'
# loop10              7:0    0   200M  0 loop
# └─lab_vg-lab_lv   253:1    0   100M  0 lvm
```

## 📚 Exercice 4 — Formater le LV (`filesystem:`)

```yaml
- name: Formater le LV en xfs
  community.general.filesystem:
    fstype: xfs
    dev: /dev/lab_vg/lab_lv
```

🔍 **Observation** :

- **Idempotent** : si le filesystem est déjà du bon type, `changed=0`.
- **`force: true`** force le reformatage si un autre filesystem existe (DANGER —
  perte de données).

**Filesystems supportés** : `ext2`, `ext3`, `ext4`, `xfs`, `btrfs`, `f2fs`, etc.

**Convention RHCE** : **xfs** est le défaut RHEL 7+ (performant pour gros
fichiers, snapshots, quotas). **ext4** reste utilisé pour `/boot`.

## 📚 Exercice 5 — Monter le LV (`mount:`)

```yaml
- name: Creer le point de montage
  ansible.builtin.file:
    path: /mnt/lvm-data
    state: directory
    mode: "0755"

- name: Monter le LV (via /dev/lab_vg/lab_lv)
  ansible.posix.mount:
    path: /mnt/lvm-data
    src: /dev/lab_vg/lab_lv
    fstype: xfs
    opts: defaults,noatime
    state: mounted
```

🔍 **Observation** :

- `/etc/fstab` contient désormais une ligne pointant vers `/dev/lab_vg/lab_lv`.
- **Mieux que d'utiliser `/dev/loopX`** : LVM gère l'**alias logique**, donc
  même si le disque change de position physique, le `/dev/<vg>/<lv>` reste
  stable.

**Pattern préféré pour fstab** : utiliser **`UUID=...`** plutôt que `/dev/...` :

```yaml
- ansible.posix.mount:
    path: /mnt/lvm-data
    src: "UUID={{ ansible_lvm.lvs.lab_lv.uuid | default('inconnu') }}"
    fstype: xfs
    state: mounted
```

L'UUID survit aux renommages — encore plus stable que LVM.

## 📚 Exercice 6 — Étendre un LV à chaud (`resizefs: true`)

Cas réel : votre `/var/log/` est plein. Vous étendez le LV **sans démonter**.

```yaml
- name: Etendre lab_lv a 150M (avec resizefs)
  community.general.lvol:
    vg: lab_vg
    lv: lab_lv
    size: 150M
    resizefs: true   # Etend le filesystem aussi
    state: present
```

🔍 **Observation** :

- **`lvextend`** étend le LV à 150Mo.
- **`resizefs: true`** lance `xfs_growfs` (ou `resize2fs` pour ext4) pour étendre
  le filesystem **sans démonter**.

**Vérifier** :

```bash
ssh ansible@db1.lab 'df -h /mnt/lvm-data'
# /dev/mapper/lab_vg-lab_lv  150M ...
```

**Limitation XFS** : `xfs_growfs` peut **étendre** mais pas **réduire**. Pour
réduire, il faut `ext4` ou démonter + reformater.

## 📚 Exercice 7 — Le piège : `vgremove` sans cleanup des LVs

```yaml
# ❌ DANGER : vgremove echoue si des LVs existent encore
- community.general.lvg:
    vg: lab_vg
    state: absent
```

Ordre correct pour le **teardown** :

```yaml
- name: 1. Demonter et retirer fstab
  ansible.posix.mount:
    path: /mnt/lvm-data
    state: absent

- name: 2. Supprimer le LV
  community.general.lvol:
    vg: lab_vg
    lv: lab_lv
    state: absent

- name: 3. Supprimer le VG
  community.general.lvg:
    vg: lab_vg
    state: absent

- name: 4. Liberer le PV
  ansible.builtin.command: pvremove -f /dev/loop10
  changed_when: true

- name: 5. Detacher le loop device
  ansible.builtin.command: losetup -d /dev/loop10
  changed_when: true
```

🔍 **Observation** : ordre **exactement inverse** de la création. Sauter une
étape = échec ou orphelins LVM.

## 🔍 Observations à noter

- **Pipeline LVM** : PV (`pvcreate`) → VG (`lvg:`) → LV (`lvol:`) → FS
  (`filesystem:`) → mount (`mount:`).
- **`size:` accepte** : valeurs absolues (`100M`), pourcentages (`50%FREE`),
  relatives (`+10G`).
- **`xfs` est le défaut RHEL 7+** ; `ext4` pour `/boot` ou besoin de réduction.
- **`resizefs: true`** étend filesystem à chaud (sans démonter).
- **`UUID=`** dans fstab > `/dev/...` — plus stable.
- **Ordre teardown** = inverse de la création.

## 🤔 Questions de réflexion

1. Vous avez `lab_vg` avec 1 PV de 200M. Vous voulez ajouter 1Go via un 2e
   disque. Quel est le pipeline complet (modules + ordre) ?

2. Pourquoi LVM préfère-t-on à des partitions classiques pour `/var/log/` ou
   `/var/lib/postgresql/` ? (indice : extensibilité, snapshots).

3. `xfs` ne sait pas réduire. Vous avez un LV 100Go en xfs avec 30Go utilisés.
   Comment passer à 50Go ? (indice : backup, recreate, restore).

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **Snapshots LVM** : `lvol: snapshot:` pour créer un snapshot point-in-time.
  Idéal avant un upgrade risqué (rollback en restaurant le snapshot).
- **Stripping** : `lvol: stripes: 2` pour répartir un LV sur plusieurs PVs
  (perf RAID 0 logique).
- **Thin provisioning** : `lvol: thinpool:` pour over-provisionner un VG —
  les LVs s'étendent à la demande.
- **`community.general.lvol_size:` avec `100%VG`** : créer un LV qui occupe
  tout le VG (cas single-LV par VG).
- **Lab 47 (mount)** : si LVM est trop complexe pour le cas, un simple loop
  device + mount peut suffire.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-rhel/lvm-storage/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-rhel/lvm-storage/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-rhel/lvm-storage/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

# Lab 48 — LVM storage : `lvg:` + `lvol:` + `filesystem:` + `mount:`

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `mise install && dsoxlab provision` à la racine du repo (cf.
> [README racine](../../../README.md#-démarrage-rapide) pour les détails).

## 🧠 Rappel

🔗 [**LVM avec Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/lvm-storage/)

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

1. **Reconnaître** le disque secondaire dédié aux labs de stockage.
2. **Construire un PV → VG → LV** en chaîne avec les 3 modules dédiés.
3. **Formater** un LV en `xfs` ou `ext4` avec idempotence.
4. **Monter** le LV via `/dev/<vg>/<lv>` dans fstab.
5. **Étendre** un LV à chaud avec `lvol: resizefs: true`.

## 🔧 Préparation

```bash
cd $ANSIBLE_TRAINING
ansible-galaxy collection install community.general ansible.posix
ansible db1.lab -m ping

# Vérifier le disque secondaire dédié aux labs de stockage
ansible db1.lab -b -m shell -a "lsblk /dev/vdb"
```

`dsoxlab run` joue le `setup.yaml` du lab, qui rend `/dev/vdb` vierge (ni
partition, ni signature LVM, ni entrée fstab résiduelle). Si vous enchaînez
depuis les labs `parted` ou `filesystem`, c'est lui qui reprend le disque.

## 📚 Exercice 1 — Repérer le disque de travail

**db1.lab** dispose d'un **disque secondaire réel** de 5 GiB, `/dev/vdb`,
provisionné par l'infra du lab (`extra_disk_gb` dans le `meta.yml` du dépôt).
C'est lui qu'on donne à LVM, pas le disque système.

```yaml
---
- name: Inspecter le disque secondaire
  hosts: db1.lab
  become: true
  tasks:
    - name: Lire la géométrie du disque
      ansible.builtin.command: lsblk /dev/vdb
      register: disk_info
      changed_when: false

    - name: Afficher
      ansible.builtin.debug:
        var: disk_info.stdout_lines
```

🔍 **Observation** : `/dev/vdb` est un device bloc de 5 GiB sans partition. LVM
sait travailler **directement sur le disque entier** : contrairement à une
partition classique, il n'y a pas besoin de passer par `parted` avant.

## 📚 Exercice 2 — Créer le PV + VG (`lvg:`)

```yaml
- name: Creer le Volume Group lab_vg sur le disque secondaire
  community.general.lvg:
    vg: lab_vg
    pvs: /dev/vdb
    state: present
```

🔍 **Observation** : le module fait **2 choses** :

1. **`pvcreate /dev/vdb`** — initialise le PV.
2. **`vgcreate lab_vg /dev/vdb`** — crée le VG sur ce PV.

**Idempotent** : 2e run → `changed=0`.

**Vérifier** :

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo vgdisplay lab_vg | head -10'
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo pvs'
```

**Étendre le VG** ultérieurement avec un nouveau disque :

```yaml
- community.general.lvg:
    vg: lab_vg
    pvs: /dev/vdb,/dev/vdc   # Ajout du 2e disque
    state: present
```

## 📚 Exercice 3 — Créer le LV (`lvol:`)

```yaml
- name: Creer le Logical Volume lab_lv (1G)
  community.general.lvol:
    vg: lab_vg
    lv: lab_lv
    size: 1G
    state: present
```

**Format de `size:`** :

- **`100M`** — taille fixe.
- **`50%FREE`** — 50% de l'espace libre du VG.
- **`+10G`** — extension de 10Go (relatif).

🔍 **Observation** : le LV est créé à `/dev/lab_vg/lab_lv` (ou
`/dev/mapper/lab_vg-lab_lv`). Visible dans `lsblk` :

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo lsblk /dev/vdb'
# vdb               252:16   0     5G  0 disk
# └─lab_vg-lab_lv   253:1    0     1G  0 lvm
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
- **Mieux que d'utiliser `/dev/vdb`** : LVM gère l'**alias logique**, donc même
  si le disque change de position physique (`vdb` devient `vdc` après un ajout
  de matériel), le `/dev/<vg>/<lv>` reste stable.

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
- name: Etendre lab_lv a 2G (avec resizefs)
  community.general.lvol:
    vg: lab_vg
    lv: lab_lv
    size: 2G
    resizefs: true   # Etend le filesystem aussi
    state: present
```

🔍 **Observation** :

- **`lvextend`** étend le LV à 2 Gio (le VG en a 5, la place est là).
- **`resizefs: true`** lance `xfs_growfs` (ou `resize2fs` pour ext4) pour étendre
  le filesystem **sans démonter**.

**Vérifier** :

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'df -h /mnt/lvm-data'
# /dev/mapper/lab_vg-lab_lv  2.0G ...
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
  ansible.builtin.command: pvremove -ff -y /dev/vdb
  changed_when: true

- name: 5. Effacer les signatures LVM du disque
  ansible.builtin.command: wipefs -af /dev/vdb
  changed_when: true
```

🔍 **Observation** : ordre **exactement inverse** de la création. Sauter une
étape = échec ou orphelins LVM. C'est exactement ce que fait le `cleanup.yaml`
du lab (`dsoxlab clean modules-rhel-lvm-storage`).

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

1. Vous avez `lab_vg` avec 1 PV de 5 Gio. Vous voulez ajouter 10 Gio via un 2e
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
- **Labs `parted` et `filesystem`** : si LVM est superflu pour le cas, une
  partition classique formatée puis montée suffit. Ils travaillent sur le même
  `/dev/vdb`, et leur `setup.yaml` reprend le disque à zéro.

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

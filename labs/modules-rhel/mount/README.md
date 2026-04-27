# Lab 47 — Module `mount:` (gérer fstab et montages)

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

🔗 [**Module mount Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/rhel-systeme/module-mount/)

`ansible.posix.mount:` gère les **points de montage Linux** : ajouter une ligne
dans `/etc/fstab`, monter immédiatement, démonter, gérer les options de montage.
C'est le module n°1 RHCE 2026 pour les **disques persistants** : volumes NFS,
disques data dédiés, swap files.

Module de la collection **`ansible.posix`**. Options critiques : **`path:`** (point
de montage), **`src:`** (device ou source), **`fstype:`** (`xfs`, `ext4`, `nfs`),
**`opts:`** (options de mount), **`state:`** (`mounted`, `unmounted`, `present`,
`absent`, `remounted`).

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Comprendre** les **5 valeurs de `state:`** : `mounted`, `unmounted`,
   `present`, `absent`, `remounted`.
2. **Distinguer** une entrée **fstab seulement** d'un **mount actif** + fstab.
3. **Monter** un loop device (fichier image) pour simuler un disque dédié.
4. **Configurer** des options de mount classiques : `noatime`, `nodev`, `nosuid`.
5. **Diagnostiquer** un montage qui ne survit pas au reboot.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible-galaxy collection install ansible.posix
ansible db1.lab -m ping

# Nettoyer un eventuel lab precedent
ansible db1.lab -b -m shell -a "umount /mnt/lab-data 2>/dev/null; rm -rf /mnt/lab-data /opt/lab-disk.img; sed -i '/lab-data/d' /etc/fstab; true"
```

## 📚 Exercice 1 — Comprendre les 5 valeurs de `state:`

| `state:` | Effet sur `/etc/fstab` | Effet runtime |
|---|---|---|
| `mounted` | Ajoute/met à jour la ligne | **Monte** le filesystem maintenant |
| `unmounted` | **Ne touche pas** à fstab | **Démonte** maintenant |
| `present` | Ajoute/met à jour la ligne | **Ne monte pas** (entrée fstab seule) |
| `absent` | **Supprime** la ligne | **Démonte** si monté |
| `remounted` | Ne touche pas à fstab | **Remount** (utile après changement d'options) |

🔍 **Cas d'usage** :

- `mounted` (le plus commun) : configurer un volume permanent avec montage immédiat.
- `present` : préparer fstab **avant** un reboot (montage différé).
- `unmounted` : démonter sans toucher à fstab (debug, maintenance).
- `absent` : retrait complet (démonter + retirer de fstab).
- `remounted` : appliquer un changement d'options sans démonter complètement.

## 📚 Exercice 2 — Créer un loop device pour simuler un disque

Sur un lab sans disque secondaire, on peut **créer un fichier image** et l'exposer
comme device bloc via `losetup`. C'est l'astuce universelle pour tester `mount:`,
LVM, parted, etc.

```yaml
---
- name: Demo mount avec loop device
  hosts: db1.lab
  become: true
  tasks:
    - name: Creer un fichier image de 100M
      ansible.builtin.command:
        cmd: dd if=/dev/zero of=/opt/lab-disk.img bs=1M count=100
        creates: /opt/lab-disk.img

    - name: Formater en ext4
      community.general.filesystem:
        fstype: ext4
        dev: /opt/lab-disk.img

    - name: Creer le point de montage
      ansible.builtin.file:
        path: /mnt/lab-data
        state: directory
        mode: "0755"
```

🔍 **Observation** :

- **`creates:`** rend `dd` idempotent (skip si fichier existe).
- Le fichier `/opt/lab-disk.img` peut être monté **directement** via `mount`
  avec l'option `loop` (ou `losetup`).
- **`community.general.filesystem:`** crée le filesystem sur le fichier — couvert
  en détail au lab 48.

## 📚 Exercice 3 — Monter avec `state: mounted`

```yaml
- name: Monter le loop device sur /mnt/lab-data
  ansible.posix.mount:
    path: /mnt/lab-data
    src: /opt/lab-disk.img
    fstype: ext4
    opts: loop,defaults,noatime
    state: mounted
```

**Lancez** :

```bash
ansible-playbook labs/modules-rhel/mount/lab.yml
ssh ansible@db1.lab 'df -h /mnt/lab-data && grep lab-data /etc/fstab'
```

🔍 **Observation** :

- `df -h` montre `/mnt/lab-data` monté avec ~95M disponibles.
- `/etc/fstab` contient la ligne :

  ```text
  /opt/lab-disk.img  /mnt/lab-data  ext4  loop,defaults,noatime  0  0
  ```

- 2e run → `changed=0` (idempotent : entrée déjà présente, déjà monté).

**`opts:`** courantes :

| Option | Effet |
|---|---|
| `defaults` | Combinaison par défaut (`rw,suid,dev,exec,auto,nouser,async`) |
| `noatime` | Pas de mise à jour de l'access time → moins d'écritures (perf) |
| `nodev` | Pas de fichiers spéciaux (devices) — sécurité |
| `nosuid` | Ignore les bits setuid — sécurité |
| `noexec` | Pas d'exécution de binaires — sécurité (`/tmp`, `/var/log`) |
| `loop` | Pour les fichiers image (auto-association `losetup`) |
| `_netdev` | Filesystem réseau (NFS, SMB) — attendre le réseau au boot |

## 📚 Exercice 4 — `state: present` vs `state: mounted`

```yaml
- name: Ajouter dans fstab SANS monter maintenant
  ansible.posix.mount:
    path: /mnt/lab-data
    src: /opt/lab-disk.img
    fstype: ext4
    opts: loop,defaults
    state: present
```

🔍 **Observation** :

- **`/etc/fstab`** est mis à jour.
- **Mais le filesystem n'est PAS monté** maintenant.
- Au prochain reboot (ou `mount -a`), le filesystem sera monté automatiquement.

**Cas d'usage** :

- Préparer la config en avance, monter manuellement après.
- Configs réseau (`_netdev`) qui ne peuvent pas être montées tant que le réseau n'est pas up.

**Vérifier** :

```bash
ssh ansible@db1.lab 'mount -a && df -h /mnt/lab-data'
```

## 📚 Exercice 5 — Démontage et retrait

```yaml
# Demonter sans toucher a fstab
- name: Demonter pour maintenance
  ansible.posix.mount:
    path: /mnt/lab-data
    state: unmounted

# Retrait complet (demonte + retire de fstab)
- name: Retrait complet
  ansible.posix.mount:
    path: /mnt/lab-data
    state: absent
```

🔍 **Observation** :

- **`state: unmounted`** : `umount /mnt/lab-data` mais l'entrée fstab reste. Au
  prochain reboot, ça remonte.
- **`state: absent`** : `umount` + suppression de la ligne fstab. Pour un retrait
  définitif.

**Piège** : si un processus utilise le filesystem (`lsof | grep /mnt/lab-data`),
le démontage échoue avec `device is busy`. Solution : tuer les processus ou
forcer avec `force: true` (dangereux, risque de corruption).

## 📚 Exercice 6 — Pattern NFS (filesystem réseau)

```yaml
- name: Monter un partage NFS
  ansible.posix.mount:
    path: /mnt/shared
    src: nfs-server.lab:/exports/shared
    fstype: nfs
    opts: rw,sync,hard,intr,_netdev
    state: mounted
```

**Options critiques NFS** :

- **`_netdev`** : indique systemd d'attendre le réseau avant de monter
  (sinon échec au boot).
- **`hard`** : retry indéfiniment en cas de coupure réseau (`soft` = échec après
  timeout — risque de corruption).
- **`intr`** : permet d'interrompre les opérations bloquées avec `Ctrl+C`.
- **`rsize=`** / **`wsize=`** : taille des buffers (defaults généralement OK).

**Sécurité** : pour NFS exposé sur Internet (déconseillé), ajouter `nosuid,nodev`.

## 📚 Exercice 7 — Le piège : entrée fstab cassée

Si vous ajoutez une ligne fstab **invalide**, le **prochain reboot échoue** avec
un dropshell systemd (`emergency mode`). Le serveur est **inaccessible en SSH**.

**Mitigation** :

```yaml
- name: Ajouter une entree (testable avant reboot)
  ansible.posix.mount:
    path: /mnt/critical
    src: /dev/critical-disk
    fstype: xfs
    opts: defaults
    state: present   # PAS mounted

- name: Tester avec mount -a (simule un reboot)
  ansible.builtin.command: mount -a
  changed_when: false
```

`mount -a` lit `/etc/fstab` et tente de monter tout. Si une entrée est
cassée, vous voyez l'erreur **maintenant** — pas après reboot.

**`backup: true`** sur le module fait un backup de fstab avant modification :

```yaml
- ansible.posix.mount:
    path: /mnt/lab-data
    src: /opt/lab-disk.img
    fstype: ext4
    state: mounted
    backup: true
```

→ Backup `/etc/fstab.<timestamp>~` créé avant modification.

## 🔍 Observations à noter

- **5 valeurs de `state:`** : `mounted`, `unmounted`, `present`, `absent`, `remounted`.
- **`mounted`** = mount maintenant + fstab (le plus commun).
- **`present`** = fstab seulement, pas de mount (préparation).
- **`opts:`** : `noatime`, `nodev`, `nosuid` pour sécurité ; `loop` pour fichiers image ;
  `_netdev` pour réseau.
- **NFS** : `hard,intr,_netdev` est le minimum.
- **Tester `mount -a`** avant un reboot pour valider fstab.
- **`backup: true`** = filet de sécurité gratuit sur fstab.

## 🤔 Questions de réflexion

1. Vous voulez monter un disque **uniquement au boot** (pas immédiatement). Quel
   `state:` ? Comment **tester** que ça marchera au reboot sans rebooter ?

2. Différence entre `mount` du module et `mount` de la commande shell. Pourquoi
   la **commande** ne modifie pas `/etc/fstab` automatiquement ?

3. Vous montez `/var/log` avec `noexec`. Quel est l'**impact** sur les services
   qui écrivent dans `/var/log/` ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`bind` mount** : monter un dossier sur un autre (`mount --bind /src /dst`).
  Useful pour exposer un sous-arbre dans un chroot ou un container.
- **`tmpfs`** : filesystem en RAM (`fstype: tmpfs`). Idéal pour `/tmp` rapide
  ou des caches volatiles.
- **`/proc/mounts`** vs **`/etc/mtab`** : `/proc/mounts` est l'état actuel kernel
  (faisant autorité). Le module peut lire l'un ou l'autre.
- **systemd `.mount` units** : alternative moderne à fstab. Pas géré par
  `mount:` mais par `template:` sur `/etc/systemd/system/<dossier>.mount`.
- **Lab 48 (lvm-storage)** : créer un PV/VG/LV sur le loop device de ce lab, pour
  un stockage extensible.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-rhel/mount/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-rhel/mount/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-rhel/mount/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.

# 🎯 Challenge — Monter un loop device persistant

## ✅ Objectif

Sur **db1.lab**, créer un fichier image `100M`, le formater en `ext4`, et le
**monter** sur `/mnt/lab-data` avec une **entrée `/etc/fstab`** (persistant
au reboot). Le montage doit **obligatoirement** porter les options
`loop,defaults,noatime,nodev,nosuid` : `loop` transforme l'image en device
loop (c'est ce qui survit au reboot), `noatime` n'enregistre pas les access
times, et `nodev,nosuid` sont les options de durcissement (pas de device node,
pas de setuid sur ce système de fichiers).

## 🧩 Étapes

1. Créer le fichier image **`/opt/lab-disk.img`** de 100 Mo (utilisez `dd` avec
   `creates:` pour idempotence).
2. **Formater** en `ext4` via `community.general.filesystem`.
3. Créer le **point de montage** `/mnt/lab-data` (mode 0755).
4. **Monter** + écrire dans **fstab** via `ansible.posix.mount` avec
   `state: mounted` et `opts: loop,defaults,noatime,nodev,nosuid`.

## 🧩 Modules clés

| Module | Rôle |
| --- | --- |
| `ansible.builtin.command` (avec `creates:`) | Créer l'image idempotemment |
| `community.general.filesystem` | Formater (ext4, xfs, …) |
| `ansible.builtin.file` | Créer le point de montage |
| `ansible.posix.mount` | Monter + gérer fstab |

## 🧩 Sémantique de `state:` du module mount

| `state:` | Effet |
| --- | --- |
| `present` | Écrit dans fstab, **ne monte pas** |
| `mounted` | Écrit dans fstab **ET** monte maintenant — c'est ce qu'on veut |
| `unmounted` | Démonte, **garde** la ligne fstab |
| `absent` | Démonte **et** supprime de fstab |

## 🧩 Options de mount

Ce challenge **impose** `opts: loop,defaults,noatime,nodev,nosuid` (séparées
par virgule). Chacune :

- `loop` — **obligatoire**, pour un fichier image (transforme `/opt/lab-disk.img`
  en device loop, et c'est ce qui fait survivre le montage à un reboot).
- `defaults` — set d'options par défaut.
- `noatime` — **obligatoire**, n'enregistre pas les access times (perf).
- `nodev,nosuid` — durcissement **obligatoire** (interdit les devices et setuid sur ce FS).

Les tests vérifient que `noatime`, `nodev` et `nosuid` sont actives sur le
montage (via `findmnt`) et toujours présentes après un reboot : les omettre
fait échouer le lab.

## 🧩 Squelette

```yaml
---
- name: Challenge - mount loop device persistant
  hosts: db1.lab
  become: true

  tasks:
    - name: Créer le fichier image 100M
      ansible.builtin.command:
        cmd: ???
        creates: ???

    - name: Formater l'image en ext4
      community.general.filesystem:
        fstype: ???
        dev: ???

    - name: Créer le point de montage
      ansible.builtin.file:
        path: ???
        state: directory
        mode: "0755"

    - name: Monter + entrée fstab
      ansible.posix.mount:
        path: ???
        src: ???
        fstype: ???
        opts: ???
        state: ???
```

> 💡 **Pièges** :
>
> - **`state:`** : `mounted` = `fstab` + montage maintenant ; `present` =
>   fstab seul (pas de montage) ; `absent` = démonte + retire fstab.
>   Pour la prod, **`mounted`** est l'option standard.
> - **`opts:`** = options fstab (champ 4). Liste séparée par virgules, ici
>   `loop,defaults,noatime,nodev,nosuid`. Sans `loop`, l'image n'est pas
>   transformée en device loop et le montage ne survit pas au reboot.
> - **`fstype: nfs`** nécessite `nfs-utils` côté managed node. Sinon
>   échec "filesystem type not supported".
> - **`backup: true`** sur `mount:` : sauvegarde `fstab` avant
>   modification — précieux en prod.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-rhel/mount/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "df -h /mnt/lab-data"
ansible db1.lab -m ansible.builtin.command -a "grep lab-data /etc/fstab"
ansible db1.lab -m ansible.builtin.command -a "mount | grep lab-data"
```

## 🧪 Validation automatisée

> ⏱️ **Un test redémarre db1** (environ 90 s). Il est marqué `slow`, et il est
> là volontairement : la persistance après redémarrage est le piège qui fait
> échouer les candidats RHCSA et RHCE, et lire le fichier de configuration
> n'en prouve rien. Le temps de vos essais, vous pouvez l'écarter :
>
> ```bash
> pytest -m 'not slow' labs/modules-rhel/mount/challenge/tests/
> ```
>
> Lancez la suite complète au moins une fois avant de considérer le
> challenge terminé.

```bash
pytest -v labs/modules-rhel/mount/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean modules-rhel-mount
```

## 💡 Pour aller plus loin

- **`state: present`** seul : on inscrit dans fstab sans monter (utile pour
  pré-configurer un host avant un disque physique branché plus tard).
- **`backup: true`** : sauvegarde `/etc/fstab` en `.bak` avant modification.
- **Pattern image-based** : utile en dev pour simuler un disque sans
  matériel. En prod, on monte plutôt un device LVM (lab 48).
- **Lint** :

   ```bash
   ansible-lint labs/modules-rhel/mount/challenge/solution.yml
   ```

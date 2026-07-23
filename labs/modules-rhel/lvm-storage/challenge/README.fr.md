# 🎯 Challenge — Pipeline LVM complet (PV → VG → LV → FS → mount)

## ✅ Objectif

Sur **db1.lab**, le disque secondaire **`/dev/vdb`** (5 GiB) est vierge : le
setup du lab l'a rendu tel, sans label ni partition. Écrivez `solution.yml`
qui amène la machine dans cet état :

1. `/dev/vdb` est initialisé en **Physical Volume** et rattaché au **Volume
   Group `lab_vg`**.
2. Un **Logical Volume `lab_lv`** de **1 GiB** est découpé dans `lab_vg`.
3. `lab_lv` porte un système de fichiers **xfs**.
4. Le volume est **monté sur `/mnt/lvm-data`** avec les options
   `defaults,noatime`, et l'entrée correspondante est dans `/etc/fstab` :
   le montage doit revenir tout seul après un reboot.
5. Un 2e run du playbook ne change rien (idempotent).

> Le PV est posé **directement sur le disque entier**, sans partition
> préalable : LVM n'en a pas besoin, et c'est le pipeline le plus courant
> pour un disque dédié.

## 🧩 Squelette à compléter

```yaml
---
- name: Challenge — pipeline LVM complet sur db1
  hosts: ???
  become: ???
  tasks:
    - name: Créer le VG sur le disque secondaire
      community.general.lvg:
        vg: ???                              # cf. objectif
        pvs: ???                             # le disque entier
        state: present

    - name: Créer le LV (cf. objectif pour la taille)
      community.general.lvol:
        vg: ???
        lv: ???
        size: ???

    - name: Formater le LV
      community.general.filesystem:
        fstype: ???
        dev: ???                             # /dev/<vg>/<lv>

    - name: Monter le LV (entrée fstab + actif maintenant)
      ansible.posix.mount:
        path: ???
        src: ???
        fstype: ???
        opts: ???                            # 2 options séparées par virgule
        state: ???                           # monte ET écrit dans fstab
```

> 💡 **Pièges** :
>
> - **Le module qui gère le VG initialise aussi le PV** : `pvcreate` puis
>   `vgcreate` en une tâche. Pas besoin d'une `command:` séparée.
> - **`state: mounted`** vs `state: present` : seul `mounted` modifie
>   `/etc/fstab` **et** monte tout de suite. `present` n'écrit que la ligne
>   fstab (rien de monté avant le prochain reboot).
> - **`noatime`** : option fstab qui supprime l'écriture du temps d'accès.
>   Les tests la cherchent dans `findmnt -no OPTIONS` **et** dans
>   `/etc/fstab` : une option passée seulement à la main au montage ne
>   survivrait pas au reboot.
> - **Le point de montage** : `state: mounted` crée le répertoire s'il
>   manque, une tâche `file:` dédiée est superflue.

## 🚀 Lancement

Une fois `solution.yml` complété, lancez-le contre `db1.lab` :

```bash
ansible-playbook labs/modules-rhel/lvm-storage/challenge/solution.yml
```

Le `PLAY RECAP` doit afficher `failed=0`. Relancez une seconde fois : un
`changed=0` confirme l'idempotence.

## 🧪 Validation

> ⏱️ **Un test redémarre db1** (environ 90 s). Il est marqué `slow`, et il est
> là volontairement : la persistance après redémarrage est le piège qui fait
> échouer les candidats RHCSA et RHCE, et lire le fichier de configuration
> n'en prouve rien. Le temps de vos essais, vous pouvez l'écarter :
>
> ```bash
> pytest -m 'not slow' labs/modules-rhel/lvm-storage/challenge/tests/
> ```
>
> Lancez la suite complète au moins une fois avant de considérer le
> challenge terminé.

```bash
pytest -v labs/modules-rhel/lvm-storage/challenge/tests/
```

Les tests vérifient sur db1 :

- `/dev/vdb` est un PV, membre du VG `lab_vg`.
- `lab_lv` existe dans `lab_vg` et fait environ 1 GiB.
- `/dev/lab_vg/lab_lv` est formaté en xfs.
- `/mnt/lvm-data` est monté sur le LV, en xfs, avec `noatime`.
- `/etc/fstab` porte l'entrée du montage (type, device et `noatime`).
- Le 2e run du playbook n'annonce plus aucun `changed`.

## 🧹 Reset

Pour rejouer le challenge dans un état neutre :

```bash
dsoxlab clean modules-rhel-lvm-storage
```

Le cleanup démonte, retire l'entrée fstab, supprime LV, VG et PV, puis rend
`/dev/vdb` vierge : vous pouvez relancer la solution from scratch.

## 💡 Pour aller plus loin

- **`ansible-lint --profile production`** : validez la qualité de votre solution.

  ```bash
  ansible-lint --profile production labs/modules-rhel/lvm-storage/challenge/solution.yml
  ```

  Sortie attendue : `Passed: 0 failure(s), 0 warning(s)`.

- **Étendre le volume** : le VG garde 4 GiB libres. Passez `lab_lv` à 2 GiB
  avec `resizefs: true` et observez `df -h /mnt/lvm-data` sans démonter.

- **Cas limites** : pensez aux scénarios d'erreur (host indisponible,
  dépendance manquante, valeur invalide) que votre solution pourrait
  rencontrer en production. Comment les gérer (`block/rescue`,
  `failed_when`, `assert`) ?

# Challenge `filesystem:`

## Énoncé

Sur **db1.lab**, le disque secondaire `/dev/vdb` est déjà partitionné en 2
par le setup du lab : `/dev/vdb1` (1 GiB) et `/dev/vdb2` (le reste).
Écrivez `solution.yml` qui amène la machine dans cet état :

1. `/dev/vdb2` porte un système de fichiers **xfs**.
2. `/dev/vdb1` est formaté en **swap**.
3. Le swap est **actif immédiatement** (`swapon --show` le liste) et
   inscrit dans `/etc/fstab` pour survivre au reboot.
4. `/dev/vdb2` est **monté sur `/mnt/data`**, avec sa propre entrée fstab.
5. Un 2e run du playbook ne change rien (idempotent).

> 🎯 **Pas de squelette ici, volontairement.** À ce stade, vous avez écrit
> assez de playbooks pour partir d'un fichier vide, et c'est exactement ce
> que demande l'EX294 : l'examen ne fournit aucun canevas. Les indices
> ci-dessous ciblent les pièges de ce module, pas la syntaxe YAML.

## Critères de réussite

> ⏱️ **Un test redémarre db1** (environ 90 s). Il est marqué `slow`, et il est
> là volontairement : la persistance après redémarrage est le piège qui fait
> échouer les candidats RHCSA et RHCE, et lire le fichier de configuration
> n'en prouve rien. Le temps de vos essais, vous pouvez l'écarter :
>
> ```bash
> pytest -m 'not slow' labs/modules-rhel/filesystem/challenge/tests/
> ```
>
> Lancez la suite complète au moins une fois avant de considérer le
> challenge terminé.

- `blkid /dev/vdb1` retourne `TYPE="swap"`, `blkid /dev/vdb2` retourne `TYPE="xfs"`.
- `swapon --show` retourne `/dev/vdb1`.
- `mount | grep /mnt/data` montre `/dev/vdb2 on /mnt/data type xfs`.
- `cat /etc/fstab` contient les 2 entrées (montage et swap).
- 2e run du playbook : `changed: 0`.

## 🧩 Bloqué ?

```bash
dsoxlab hint modules-rhel-filesystem
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

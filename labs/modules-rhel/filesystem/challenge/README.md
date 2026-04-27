# Challenge `filesystem:`

## Énoncé

Sur **db1.lab** avec `/dev/vdb` partitionné (lab `parted` complété),
écrivez `solution.yml` qui :

1. Crée un **xfs** sur `/dev/vdb2`.
2. Crée un **swap** sur `/dev/vdb1` (passé en flag swap par `parted` au
   préalable, sinon avec `force: true`).
3. **Active** le swap immédiatement (`swapon`) et ajoute l'entrée dans
   `/etc/fstab` avec `ansible.posix.mount`.
4. Monte `/dev/vdb2` sur `/mnt/data` avec entrée fstab.
5. Vérifie :
   - `swapon --show` montre `/dev/vdb1`.
   - `df -hT /mnt/data` montre xfs.
   - 2e run = `ok` (idempotent).

## Critères de réussite

- `swapon --show` retourne `/dev/vdb1`.
- `mount | grep /mnt/data` montre `/dev/vdb2 on /mnt/data type xfs`.
- `cat /etc/fstab` contient les 2 entrées.
- 2e run du playbook : `changed: 0`.

## Indices

- `fstype: swap` lance `mkswap`.
- `swapon` n'est pas couvert par `filesystem:` directement — utiliser
  `ansible.posix.mount` avec `path: none, fstype: swap, opts: sw, state: mounted`.
- Pour `xfs`, le `state: mounted` du module `mount` peut nécessiter le
  fs créé d'abord.

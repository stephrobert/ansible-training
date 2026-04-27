# 🎯 Challenge — Pipeline LVM complet (PV → VG → LV → FS → mount)

## ✅ Objectif

Écrire `solution.yml` qui sur **db1.lab** :

1. Crée un fichier image `/opt/lab-lvm.img` de 500Mo (xfs nécessite ≥ 300M).
2. L'associe à `/dev/loop10` via `losetup`.
3. Crée un PV puis un VG **`lab_vg`** sur `/dev/loop10`.
4. Crée un LV **`lab_lv`** de 300M dans `lab_vg`.
5. Formate `lab_lv` en **xfs**.
6. Monte sur `/mnt/lvm-data` avec options `defaults,noatime`.

## 🧩 Squelette à compléter

```yaml
---
- name: Challenge — pipeline LVM complet sur db1
  hosts: ???
  become: ???
  tasks:
    - name: Créer le fichier image (cf. objectif pour la taille)
      ansible.builtin.command:
        cmd: dd if=/dev/zero of=/opt/lab-lvm.img bs=1M count=???
        creates: ???                         # idempotence : ne crée que si absent

    - name: Associer le fichier au loop device 10 (idempotent)
      ansible.builtin.shell: |
        if ! losetup /dev/loop10 2>/dev/null; then
          losetup /dev/loop10 /opt/lab-lvm.img
          echo CHANGED
        fi
      register: loop_setup
      changed_when: "'CHANGED' in loop_setup.stdout"

    - name: Créer le VG sur le loop device
      community.general.lvg:
        vg: ???                              # cf. objectif
        pvs: ???
        state: present

    - name: Créer le LV (cf. objectif pour la taille)
      community.general.lvol:
        vg: ???
        lv: ???
        size: ???                            # XFS exige ≥ 300M

    - name: Formater le LV
      community.general.filesystem:
        fstype: ???
        dev: ???                             # /dev/<vg>/<lv>

    - name: Créer le point de montage
      ansible.builtin.file:
        path: ???                            # /mnt/lvm-data
        state: ???                           # répertoire
        mode: "0755"

    - name: Monter le LV (entrée fstab + actif maintenant)
      ansible.posix.mount:
        path: ???
        src: ???
        fstype: ???
        opts: ???                            # 2 options séparées par virgule
        state: ???                           # 'mounted' = monte + ajoute fstab
```

> 💡 **Pièges** :
>
> - **Taille XFS minimum** : XFS refuse de formater un device < 300 Mo.
>   Si vous suivez aveuglément un tutoriel avec un LV de 100 Mo, le
>   `mkfs.xfs` échoue avec un message cryptique. Lisez l'objectif et
>   alignez les tailles.
> - **Idempotence du `losetup`** : `losetup /dev/loop10 file` échoue si
>   loop10 est déjà associé. Le `shell` avec `if !` ci-dessus gère ça.
>   Alternative : module `community.general.system.lvg` qui détecte
>   automatiquement, ou `losetup -j <file>` pour vérifier l'association.
> - **`state: mounted`** vs `state: present` : seul `mounted` modifie
>   `/etc/fstab` **et** monte tout de suite. `present` ne fait que
>   `fstab` (pas de mount immédiat).
> - **`noatime`** : option `fstab` qui désactive la mise à jour du temps
>   d'accès (économise des écritures). Le test la cherche dans
>   `findmnt -no OPTIONS`.

## 🚀 Lancement

Une fois `solution.yml` complété, lancez-le contre `db1.lab` :

```bash
ansible-playbook labs/modules-rhel/lvm-storage/challenge/solution.yml
```

Le `PLAY RECAP` doit afficher `failed=0`. Relancez une seconde fois : un
`changed=0` confirme que les tâches `command:`/`shell:` sont bien protégées
par `creates:` ou un test conditionnel (idempotence préservée).

## 🧪 Validation

```bash
pytest -v labs/modules-rhel/lvm-storage/challenge/tests/
```

Le test pytest+testinfra vérifie sur db1 :

- `/opt/lab-lvm.img` existe (~200Mo).
- `/dev/loop10` est associé.
- `lab_vg` existe avec 1 PV.
- `lab_lv` existe (100Mo).
- `/dev/lab_vg/lab_lv` est en xfs.
- `/mnt/lvm-data` est monté avec `noatime`.

## 🧹 Reset

Pour rejouer le challenge dans un état neutre :

```bash
make -C labs/modules-rhel/lvm-storage/ clean
```

Cette cible désinstalle/supprime ce que la solution a posé sur les managed
nodes (paquets, fichiers, services, règles firewall) afin que vous puissiez
relancer la solution from scratch.

## 💡 Pour aller plus loin

- **`ansible-lint --profile production`** : validez la qualité de votre solution.

  ```bash
  ansible-lint --profile production labs/modules-rhel/lvm-storage/challenge/solution.yml
  ```

  Sortie attendue : `Passed: 0 failure(s), 0 warning(s)`.

- **Idempotence** : relancez la solution une seconde fois — un `PLAY RECAP`
  avec `changed=0` partout confirme un playbook propre.

- **Cas limites** : pensez aux scénarios d'erreur (host indisponible,
  dépendance manquante, valeur invalide) que votre solution pourrait
  rencontrer en production. Comment les gérer (`block/rescue`,
  `failed_when`, `assert`) ?

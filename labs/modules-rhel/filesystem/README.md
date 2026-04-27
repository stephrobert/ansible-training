# Lab — Module `filesystem:` (créer un système de fichiers)

> ⚠️ **Lab destructif.** Manipule un **disque réel**. Toujours sur **VM jetable**.
>
> 💡 **Lab autonome.** Pré-requis : 2 partitions cibles (`/dev/vdb1`, `/dev/vdb2`
> sur disque réel ou `/dev/loop0p1`, `/dev/loop0p2` via loopback) **d'au moins
> 400 MiB chacune** (xfs requiert 300 MiB minimum), et
> `ansible-galaxy collection install community.general`.

## 🧠 Rappel

🔗 [**Module filesystem Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-filesystem/)

`community.general.filesystem:` crée un **système de fichiers** sur une
partition ou un volume logique : `ext4`, `xfs`, `btrfs`, `f2fs`, `swap`. C'est
l'étape **après la partition** et **avant le mount**.

**Important** : le module ne **détruit jamais** un fs existant par défaut —
protection contre la perte de données. Il faut `force: true` pour forcer.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Créer** un fs ext4 et xfs sur 2 partitions.
2. **Choisir** le bon fstype selon le cas d'usage.
3. **Comprendre** le minimum 300 MiB de xfs (validé en lab).
4. **Forcer** la recréation avec `force: true`.

## 🔧 Préparation

**Variante A — vrai disque** :

```bash
# Avec /dev/vdb partitionné (cf. lab parted)
ansible db1.lab -b -m shell -a "ls /dev/vdb1 /dev/vdb2"
```

**Variante B — loopback 800 MiB minimum** :

```bash
ansible db1.lab -b -m shell -a "
  losetup -d /dev/loop0 2>/dev/null || true
  rm -f /var/tmp/lab-disk.img
  dd if=/dev/zero of=/var/tmp/lab-disk.img bs=1M count=800 status=none
  losetup -fP /var/tmp/lab-disk.img
  parted -s /dev/loop0 mklabel gpt
  parted -s /dev/loop0 mkpart boot 0% 50%
  parted -s /dev/loop0 mkpart data 50% 100%
  partprobe /dev/loop0
  ls /dev/loop0p1 /dev/loop0p2"
```

> ⚠️ **Le loopback doit faire au moins 800 MiB** pour permettre 2 partitions
> de 400 MiB. xfs refuse les filesystems < 300 MiB avec `Filesystem must be
> larger than 300MB`.

## 📚 Exercice 1 — Créer ext4 + xfs

```yaml
---
- name: Demo filesystem
  hosts: db1.lab
  become: true
  tasks:
    - name: Créer ext4
      community.general.filesystem:
        fstype: ext4
        dev: /dev/loop0p1     # ou /dev/vdb1
        state: present

    - name: Créer xfs
      community.general.filesystem:
        fstype: xfs
        dev: /dev/loop0p2     # ou /dev/vdb2
        state: present
```

Lancez 2 fois et vérifiez l'idempotence (2e run = `ok`).
Vérifiez : `blkid /dev/loop0p1 /dev/loop0p2` retourne `TYPE="ext4"` et `TYPE="xfs"`.

## 📚 Exercice 2 — Protection contre la destruction

Tentez de changer le fstype sans `force` :

```yaml
- community.general.filesystem:
    fstype: xfs       # alors que vdb1/loop0p1 est en ext4
    dev: /dev/loop0p1
```

**Observer** : task **`failed`** — le module refuse d'écraser un fs existant.

Pour forcer (perte de données acceptée) :

```yaml
- community.general.filesystem:
    fstype: xfs
    dev: /dev/loop0p1
    force: true
```

## 🔍 Observations à noter

- **Idempotence** : un second run du playbook doit afficher `changed=0` sur
  toutes les tâches du module `community.general.filesystem`. Si une tâche reste `changed=1`, c'est
  que la regex/condition n'est pas ancrée correctement (cf. exercices).
- **FQCN explicite** : `community.general.filesystem` (et non son nom court) — `ansible-lint
  --profile production` le vérifie.
- **`validate:`** quand c'est disponible (lineinfile, copy, template) : un
  binaire externe contrôle la syntaxe du fichier avant écriture, ce qui évite
  de casser un service avec une config invalide.
- **Convention de ciblage** : ce lab cible **db1.lab** (un seul host pour
  isoler l'impact destructif).

## 🤔 Questions de réflexion

1. Quand utiliser `community.general.filesystem` plutôt que `command: mkfs.<fstype>` (non idempotent — il faut tester si déjà formaté) ? Listez 2 cas où chaque
   alternative serait préférable (lisibilité, idempotence, performance).

2. Si vous deviez créer un filesystem (ext4, xfs, swap) sur un device block sur **50 serveurs en parallèle**, quels
   paramètres Ansible (`forks`, `serial`, `strategy`) ajusteriez-vous pour
   tenir un SLA de 5 minutes ?

3. Comment gérer le cas où le module échoue **partiellement** (succès sur
   certaines tâches, échec sur d'autres) ? Quelles stratégies permettent de
   reprendre sans tout rejouer (`block/rescue`, `--start-at-task`, marqueur
   d'état) ?

## 🚀 Challenge final

Une fois les exercices ci-dessus digérés, lancez le **challenge autonome** :

```bash
$ANSIBLE_TRAINING/bin/dsoxlab lab modules-rhel/filesystem --challenge
# ou
cat labs/modules-rhel/filesystem/challenge/README.md
```

Le challenge demande d'écrire votre `challenge/solution.yml` sans regarder
les exercices. Validation par `pytest` :

```bash
pytest -v labs/modules-rhel/filesystem/challenge/tests/
```

## 💡 Pour aller plus loin

- Combinez `community.general.filesystem` avec **`backup: true`** pour conserver une copie
  horodatée du fichier original avant modification — utile pour rollback.
- Étudiez **`check_mode: true`** + `--diff` : Ansible vous montre ce qu'il
  ferait sans rien appliquer. Indispensable en production.
- Comparez la **performance** entre 1 tâche `community.general.filesystem` × 10 et 1 tâche
  `template:` qui génère le fichier complet en une fois — souvent le
  template est plus rapide ET plus lisible quand le nombre de modifs grossit.

## 🧹 Cleanup

```bash
make clean
```

## 📂 Solution

Voir `solution/modules-rhel/filesystem/solution.yml` (validée en lab le
2026-04-30 sur loopback 800 MiB, AlmaLinux 10, ansible-core 2.18,
community.general 12.x).

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/modules-rhel/filesystem/lab.yml
ansible-lint labs/modules-rhel/filesystem/challenge/solution.yml
ansible-lint --profile production labs/modules-rhel/filesystem/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques RHCE 2026.


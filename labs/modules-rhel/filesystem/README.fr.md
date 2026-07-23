# Lab — Module `filesystem:` (créer un système de fichiers)

> ⚠️ **Lab destructif.** Manipule un **disque réel**. Toujours sur **VM jetable**.
>
> 💡 **Lab autonome.** Pré-requis : `ansible-galaxy collection install
> community.general ansible.posix`. Le `setup.yaml` du lab partitionne le
> disque secondaire **`/dev/vdb`** de **db1.lab** en 2 : `/dev/vdb1` (1 GiB)
> et `/dev/vdb2` (le reste). Les deux dépassent largement les **300 MiB**
> qu'exige xfs.

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

Le `setup.yaml` du lab, joué par `dsoxlab run`, remet `/dev/vdb` à zéro puis
pose les 2 partitions de travail. Vérifiez qu'elles sont là :

```bash
ansible db1.lab -b -m shell -a "lsblk /dev/vdb"
```

> ⚠️ **xfs refuse les filesystems < 300 MiB** (`Filesystem must be larger than
> 300MB`). Les partitions posées par le setup (1 GiB et ~4 GiB) sont
> dimensionnées pour passer sans y penser.

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
        dev: /dev/vdb1
        state: present

    - name: Créer xfs
      community.general.filesystem:
        fstype: xfs
        dev: /dev/vdb2
        state: present
```

Lancez 2 fois et vérifiez l'idempotence (2e run = `ok`).
Vérifiez : `blkid /dev/vdb1 /dev/vdb2` retourne `TYPE="ext4"` et `TYPE="xfs"`.

> 💡 Le **challenge** de ce lab demande un **swap** sur `/dev/vdb1`, pas un
> ext4 : cet exercice sert à voir le module à l'œuvre sur 2 fstypes.

## 📚 Exercice 2 — Protection contre la destruction

Tentez de changer le fstype sans `force` :

```yaml
- community.general.filesystem:
    fstype: xfs       # alors que vdb1 est en ext4
    dev: /dev/vdb1
```

**Observer** : task **`failed`** — le module refuse d'écraser un fs existant.

Pour forcer (perte de données acceptée) :

```yaml
- community.general.filesystem:
    fstype: xfs
    dev: /dev/vdb1
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
`dsoxlab clean <id-du-lab>`
```

## 📂 Solution

Voir `solution/modules-rhel/filesystem/solution.yml` (validée sur le disque
secondaire réel `/dev/vdb`, AlmaLinux 9, ansible-core 2.18,
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

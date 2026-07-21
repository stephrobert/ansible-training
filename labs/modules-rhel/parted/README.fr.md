# Lab — Module `parted:` (créer une partition disque)

> ⚠️ **Lab destructif.** Manipule un **disque réel**. Toujours utiliser
> une **VM jetable** ou un **disque vierge**. Une mauvaise unité = données
> perdues.
>
> 💡 **Lab autonome.** Pré-requis : `ansible-galaxy collection install
> community.general`. Le disque secondaire **`/dev/vdb`** (5 GiB) de
> **db1.lab** est provisionné par l'infra du lab.

## 🧠 Rappel

🔗 [**Module parted Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-parted/)

`community.general.parted:` crée, supprime, et inspecte des **partitions
disque** Linux (MBR ou GPT) en idempotent. C'est le **prérequis brut** avant
tout `filesystem:` ou `lvg:`.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Créer** une partition primaire alignée sur un disque vierge.
2. Choisir entre **MBR** et **GPT** selon le contexte.
3. **Combiner** plusieurs partitions sans chevauchement.
4. Poser des **flags** (`lvm`, `boot`, `esp`).
5. **Inspecter** la table de partitions existante.

## 🔧 Préparation

**db1.lab** dispose d'un **disque secondaire réel** de 5 GiB, `/dev/vdb`,
provisionné par l'infra du lab (`extra_disk_gb` dans le `meta.yml` du dépôt) :

```bash
ansible db1.lab -b -m shell -a "lsblk /dev/vdb"
```

`dsoxlab run` joue le `setup.yaml` du lab, qui rend `/dev/vdb` vierge (ni
partition, ni signature de système de fichiers, ni entrée fstab résiduelle).
Si vous enchaînez depuis les labs `filesystem` ou `lvm-storage`, qui partagent
la même VM et le même disque, c'est lui qui reprend le disque à zéro.

## 📚 Exercice 1 — Créer une partition GPT

```yaml
---
- name: Demo parted — partition unique
  hosts: db1.lab
  become: true
  tasks:
    - name: Créer une partition GPT de 50 %
      community.general.parted:
        device: /dev/vdb
        number: 1
        state: present
        label: gpt
        part_start: "0%"
        part_end: "50%"
        name: "data"
```

**Vérifier** : `lsblk /dev/vdb` montre `vdb1`, `parted -s /dev/vdb print` montre
`Partition Table: gpt`.

## 📚 Exercice 2 — Plusieurs partitions sans flags

```yaml
- name: Partition 2 — reste du disque
  community.general.parted:
    device: /dev/vdb
    number: 2
    state: present
    part_start: "50%"
    part_end: "100%"
    name: "lvm"
```

## 📚 Exercice 3 — Inspecter sans modifier

```yaml
- name: Inspecter /dev/vdb
  community.general.parted:
    device: /dev/vdb
  register: vdb_info

- ansible.builtin.debug:
    msg: "{{ vdb_info.partitions }}"
```

## ⚠️ Note sur les flags

Sur **GPT**, les flags valides sont `boot`, `bios_grub`, `esp`, `lvm`, `raid`,
`legacy_boot`, etc. Sur **MBR**, ce sont `boot`, `lba`, `lvm`, etc. Le flag
`boot` sur GPT peut faire basculer la table en MBR — **préférer `esp`** pour
l'EFI System Partition, et `lvm` pour les PV LVM.

## 🔍 Observations à noter

- **Idempotence** : un second run du playbook doit afficher `changed=0` sur
  toutes les tâches du module `community.general.parted`. Si une tâche reste `changed=1`, c'est
  que la regex/condition n'est pas ancrée correctement (cf. exercices).
- **FQCN explicite** : `community.general.parted` (et non son nom court) — `ansible-lint
  --profile production` le vérifie.
- **`validate:`** quand c'est disponible (lineinfile, copy, template) : un
  binaire externe contrôle la syntaxe du fichier avant écriture, ce qui évite
  de casser un service avec une config invalide.
- **Convention de ciblage** : ce lab cible **db1.lab** (un seul host pour
  isoler l'impact destructif).

## 🤔 Questions de réflexion

1. Quand utiliser `community.general.parted` plutôt que `command: parted ...` (non idempotent — recréerait à chaque run) ? Listez 2 cas où chaque
   alternative serait préférable (lisibilité, idempotence, performance).

2. Si vous deviez partitionner un disque (GPT/MSDOS, flags, taille) sur **50 serveurs en parallèle**, quels
   paramètres Ansible (`forks`, `serial`, `strategy`) ajusteriez-vous pour
   tenir un SLA de 5 minutes ?

3. Comment gérer le cas où le module échoue **partiellement** (succès sur
   certaines tâches, échec sur d'autres) ? Quelles stratégies permettent de
   reprendre sans tout rejouer (`block/rescue`, `--start-at-task`, marqueur
   d'état) ?

## 🚀 Challenge final

Une fois les exercices ci-dessus digérés, lancez le **challenge autonome** :

```bash
$ANSIBLE_TRAINING/bin/dsoxlab lab modules-rhel/parted --challenge
# ou
cat labs/modules-rhel/parted/challenge/README.md
```

Le challenge demande d'écrire votre `challenge/solution.yml` sans regarder
les exercices. Validation par `pytest` :

```bash
pytest -v labs/modules-rhel/parted/challenge/tests/
```

## 💡 Pour aller plus loin

- Combinez `community.general.parted` avec **`backup: true`** pour conserver une copie
  horodatée du fichier original avant modification — utile pour rollback.
- Étudiez **`check_mode: true`** + `--diff` : Ansible vous montre ce qu'il
  ferait sans rien appliquer. Indispensable en production.
- Comparez la **performance** entre 1 tâche `community.general.parted` × 10 et 1 tâche
  `template:` qui génère le fichier complet en une fois — souvent le
  template est plus rapide ET plus lisible quand le nombre de modifs grossit.

## 🧹 Cleanup

```bash
`dsoxlab clean <id-du-lab>`
```

⚠️ Le cleanup **détruit** la table de partitions de `/dev/vdb`.

## 📂 Solution

Voir `solution/modules-rhel/parted/solution.yml` (validée sur le disque
secondaire réel `/dev/vdb`).

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/modules-rhel/parted/lab.yml
ansible-lint labs/modules-rhel/parted/challenge/solution.yml
ansible-lint --profile production labs/modules-rhel/parted/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques RHCE 2026.

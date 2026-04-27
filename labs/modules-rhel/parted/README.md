# Lab — Module `parted:` (créer une partition disque)

> ⚠️ **Lab destructif.** Manipule un **disque réel**. Toujours utiliser
> une **VM jetable** ou un **disque vierge**. Une mauvaise unité = données
> perdues.
>
> 💡 **Lab autonome.** Pré-requis : VM avec **`/dev/vdb` réel** (idéal) ou
> un fichier loopback (cf. section « Préparation »), et
> `ansible-galaxy collection install community.general`.

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

**Variante A — VM avec disque secondaire `/dev/vdb`** (recommandé) :

```bash
ansible db1.lab -b -m shell -a "lsblk /dev/vdb"
```

**Variante B — fichier loopback** (si pas de disque secondaire) :

```bash
ansible db1.lab -b -m shell -a "
  test -f /var/tmp/lab-disk.img || dd if=/dev/zero of=/var/tmp/lab-disk.img bs=1M count=800 status=none
  losetup -fP --show /var/tmp/lab-disk.img"
```

> ⚠️ **Limite connue du loopback** validée en lab : sur AlmaLinux 10 + ansible-core 2.18 +
> `community.general 12.x`, le module `community.general.parted` **bascule la
> table en `msdos` même quand vous demandez `label: gpt`**, ne crée que la
> 2e partition, et perd l'idempotence. Bug confirmé sur loop devices, **pas
> sur disque réel**. Pour ce lab, **ajoutez un vrai disque** à votre VM
> (`virsh attach-disk`) ou utilisez `parted` en CLI direct (validé) avant le
> module.

## 📚 Exercice 1 — Créer une partition GPT (sur `/dev/vdb` réel)

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
make clean
```

⚠️ Le cleanup **détruit** la table de partitions de `/dev/vdb`.

## 📂 Solution

Voir `solution/modules-rhel/parted/solution.yml` (validée sur disque réel ;
pour loopback, la solution utilise `parted` CLI en preflight pour contourner
le bug du module).

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


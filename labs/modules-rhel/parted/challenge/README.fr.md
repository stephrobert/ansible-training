# Découper le nouveau disque avant que le stockage ne le réclame

## La situation

Un second disque vient d'être rattaché à **db1.lab** et il arrive brut : ni
label, ni partition. Le découpage cible est arrêté et vient de l'architecture :
une petite partition de boot EFI, une partition de taille fixe pour un système
de fichiers, et tout le reste confié à LVM pour que les volumes puissent grandir
plus tard. Ce qui compte autant que le découpage, c'est que ce playbook sera
rejoué, sur cet hôte et sur les vingt suivants : **un outil de partitionnement
qui se rejoue est un outil qui détruit des données**, sauf s'il reconnaît ce qui
existe déjà.

Votre mission :

1. Depuis **control-node.lab**, poser un **label GPT** sur le nouveau disque de
   **db1.lab**, puis tailler la **partition de boot de 500 Mio** avec les flags
   qu'exige une partition EFI.
2. Ajouter la **partition de 4 Gio** destinée à un système de fichiers, chaînée
   juste après la première, sans trou ni chevauchement.
3. Confier le **reste du disque** à une troisième partition marquée pour LVM,
   sans figer une taille qui casserait sur un disque de dimension différente.
4. Prouver l'**idempotence** : le second passage doit afficher `changed: 0`, et
   présenter la table obtenue avec ses flags.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-parted/

## Challenge `parted:`

### Énoncé

Sur **db1.lab** avec un disque secondaire **`/dev/vdb`**, écrivez
`solution.yml` qui :

1. Crée 3 partitions GPT sur `/dev/vdb` :
   - `vdb1` : 500 MiB, flag `[boot, esp]`.
   - `vdb2` : 4 GiB, sans flag particulier (pour ext4).
   - `vdb3` : reste du disque, flag `[lvm]`.
2. Vérifie idempotence avec un 2e run.
3. Inspecte la table finale et l'affiche via `debug`.

> 🎯 **Pas de squelette ici, volontairement.** À ce stade, vous avez écrit
> assez de playbooks pour partir d'un fichier vide, et c'est exactement ce
> que demande l'EX294 : l'examen ne fournit aucun canevas. Les indices
> ci-dessous ciblent les pièges de ce module, pas la syntaxe YAML.

### Critères de réussite

- `lsblk /dev/vdb` montre 3 partitions avec les bonnes tailles.
- 2e run du playbook → **`changed: 0`** (idempotent).
- Le `debug` affiche les 3 partitions avec leurs flags respectifs.

### 🧩 Bloqué ?

```bash
dsoxlab hint modules-rhel-parted
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

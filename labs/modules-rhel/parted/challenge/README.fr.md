# Challenge `parted:`

## Énoncé

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

## Critères de réussite

- `lsblk /dev/vdb` montre 3 partitions avec les bonnes tailles.
- 2e run du playbook → **`changed: 0`** (idempotent).
- Le `debug` affiche les 3 partitions avec leurs flags respectifs.

## 🧩 Bloqué ?

```bash
dsoxlab hint modules-rhel-parted
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

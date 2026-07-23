# Challenge `lineinfile:`

## Énoncé

Sur **db1.lab**, écrivez un playbook **`solution.yml`** qui :

1. **Désactive** le login root SSH (`PermitRootLogin no`).
2. Réduit **MaxAuthTries** à `3` (en gardant l'indentation existante via `backrefs`).
3. Ajoute la ligne **`AllowUsers ansible`** si absente.
4. **Valide** chaque modif avec `sshd -t -f %s` avant écriture.
5. Notifie un **handler** `Restart sshd` qui ne se déclenche qu'à la fin si
   au moins une des 3 tâches a `changed`.

> 🎯 **Pas de squelette ici, volontairement.** À ce stade, vous avez écrit
> assez de playbooks pour partir d'un fichier vide, et c'est exactement ce
> que demande l'EX294 : l'examen ne fournit aucun canevas. Les indices
> ci-dessous ciblent les pièges de ce module, pas la syntaxe YAML.

## Critères de réussite

- Premier run : `changed: 3` ou plus selon l'état initial.
- Deuxième run : **`changed: 0`** (idempotence stricte).
- `sshd -T | grep -E "PermitRootLogin|MaxAuthTries|AllowUsers"` retourne les 3 lignes attendues.
- `sshd -t` ne renvoie **aucune** erreur.

## 🧩 Bloqué ?

```bash
dsoxlab hint modules-fichiers-lineinfile
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

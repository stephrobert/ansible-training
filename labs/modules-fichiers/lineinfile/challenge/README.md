# Challenge `lineinfile:`

## Énoncé

Sur **db1.lab**, écrivez un playbook **`solution.yml`** qui :

1. **Désactive** le login root SSH (`PermitRootLogin no`).
2. Réduit **MaxAuthTries** à `3` (en gardant l'indentation existante via `backrefs`).
3. Ajoute la ligne **`AllowUsers ansible`** si absente.
4. **Valide** chaque modif avec `sshd -t -f %s` avant écriture.
5. Notifie un **handler** `Restart sshd` qui ne se déclenche qu'à la fin si
   au moins une des 3 tâches a `changed`.

## Critères de réussite

- Premier run : `changed: 3` ou plus selon l'état initial.
- Deuxième run : **`changed: 0`** (idempotence stricte).
- `sshd -T | grep -E "PermitRootLogin|MaxAuthTries|AllowUsers"` retourne les 3 lignes attendues.
- `sshd -t` ne renvoie **aucune** erreur.

## Indices

- Pour l'idempotence avec `backrefs: true`, la regexp doit matcher à la fois
  la ligne d'origine et la ligne après modification — utilisez un groupe
  qui capture le préfixe (espaces + nom du paramètre).
- `AllowUsers` peut ne pas exister du tout — utiliser un `lineinfile:` sans
  `backrefs` pour cette tâche-là.

# 🎯 Challenge — Tags spéciaux `always` et `never`

Vous savez utiliser `tags: install`. Le challenge ajoute deux tags spéciaux :

- **`always`** : la tâche s'exécute **même si** l'apprenant lance avec `--tags configuration`.
- **`never`** : la tâche ne s'exécute **jamais** sauf si on lance explicitement `--tags reset`.

## ✅ Objectif

Écrire `solution.yml` qui cible `db1.lab` et contient :

1. Une tâche **`Marqueur always`** taguée `always` qui pose
   `/tmp/challenge-tag-always.txt`
2. Une tâche **`Marqueur configuration`** taguée `configuration` qui pose
   `/tmp/challenge-tag-configuration.txt`
3. Une tâche **`Marqueur reset destructif`** taguée `[never, reset]` qui pose
   `/tmp/challenge-tag-reset.txt` et **supprime** `/tmp/challenge-tag-configuration.txt`
   et `/tmp/challenge-tag-always.txt`

## 🧩 Consignes

1. Créez `challenge/solution.yml`.
2. Lancez avec `--tags configuration` :

   ```bash
   ansible-playbook labs/07-ecrire-code-tags/challenge/solution.yml --tags configuration
   ```

   Attendu :
   - `/tmp/challenge-tag-always.txt` existe (toujours)
   - `/tmp/challenge-tag-configuration.txt` existe (taggé configuration)
   - `/tmp/challenge-tag-reset.txt` n'existe **pas** (taggé `never`)

3. **Ne lancez pas** la commande `--tags reset` (elle est destructive et
   ferait échouer les tests). Le test vérifie que reset n'a pas tourné.

## 🧪 Validation

Le script `tests/test_tags.py` vérifie sur **db1.lab** :

- `/tmp/challenge-tag-always.txt` existe (preuve `always`)
- `/tmp/challenge-tag-configuration.txt` existe (preuve `--tags configuration`)
- `/tmp/challenge-tag-reset.txt` **n'existe PAS** (preuve `never` non déclenché)

```bash
pytest -v labs/07-ecrire-code-tags/challenge/tests/
```

## 🚀 Pour aller plus loin

- Refaites le challenge en lançant **sans `--tags`** : `always` tourne,
  `configuration` aussi, `never` toujours skippé.
- Lancez avec **`--tags reset`** : `always` tourne, `reset` aussi, et les
  fichiers configuration/always sont supprimés. Vérifie ensuite avec un
  `ls /tmp/challenge-tag-*.txt`.

---

Bonne chance ! 🧠

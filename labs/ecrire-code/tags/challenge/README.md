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

Squelette à compléter :

```yaml
---
- name: Lab 07 — démontrer always + never + configuration
  hosts: ???
  become: ???
  gather_facts: false
  tasks:
    - name: Marqueur always
      ansible.builtin.file:
        path: ???
        state: ???                   # touch
      tags: ???

    - name: Marqueur configuration
      ansible.builtin.file:
        path: ???
        state: ???
      tags: ???

    - name: Marqueur reset destructif (multi-tags)
      ansible.builtin.shell: |
        touch ???
        rm -f ??? ???
      tags: [???, ???]               # never + reset
```

1. Créez `challenge/solution.yml` à partir du squelette.
2. Lancez avec `--tags configuration` :

   ```bash
   ansible-playbook labs/ecrire-code/tags/challenge/solution.yml --tags configuration
   ```

   Attendu :
   - `/tmp/challenge-tag-always.txt` existe (toujours)
   - `/tmp/challenge-tag-configuration.txt` existe (taggé configuration)
   - `/tmp/challenge-tag-reset.txt` n'existe **pas** (taggé `never`)

3. **Ne lancez pas** la commande `--tags reset` (elle est destructive et
   ferait échouer les tests). Le test vérifie que reset n'a pas tourné.

> 💡 **Pièges** :
>
> - **`always`** s'exécute **même avec `--tags X`** (où X ≠ always).
>   Pour le skipper : `--skip-tags always`.
> - **`never`** s'exécute **uniquement** si demandé explicitement par
>   `--tags <son_tag>`. Sans `--tags`, il est skippé.
> - **Multi-tags** : `tags: [a, b]` permet à la tâche de matcher `--tags a`
>   OU `--tags b`. Pour matcher les deux, il faudrait `--tags a,b`.
> - **Le conftest** lance le replay avec `--tags configuration` (cf.
>   `_EXTRA_ARGS`). Si vous ajoutez d'autres tags, pensez à mettre à jour.

## 🧪 Validation

Le script `tests/test_tags.py` vérifie sur **db1.lab** :

- `/tmp/challenge-tag-always.txt` existe (preuve `always`)
- `/tmp/challenge-tag-configuration.txt` existe (preuve `--tags configuration`)
- `/tmp/challenge-tag-reset.txt` **n'existe PAS** (preuve `never` non déclenché)

```bash
pytest -v labs/ecrire-code/tags/challenge/tests/
```

## 🚀 Pour aller plus loin

- Refaites le challenge en lançant **sans `--tags`** : `always` tourne,
  `configuration` aussi, `never` toujours skippé.
- Lancez avec **`--tags reset`** : `always` tourne, `reset` aussi, et les
  fichiers configuration/always sont supprimés. Vérifie ensuite avec un
  `ls /tmp/challenge-tag-*.txt`.

---

Bonne chance ! 🧠

## 🧹 Reset

Pour rejouer le challenge dans un état neutre :

```bash
make -C labs/ecrire-code/tags/ clean
```

Cette cible désinstalle/supprime ce que la solution a posé sur les managed
nodes (paquets, fichiers, services, règles firewall) afin que vous puissiez
relancer la solution from scratch.

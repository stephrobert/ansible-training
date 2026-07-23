# 🎯 Challenge — Combiner `import_tasks` + `include_tasks` + boucle

## ✅ Objectif

Écrire un playbook qui combine les **3 patterns** (`import_tasks` static + `include_tasks` avec `loop:` + 1 tâche à part) et dépose **4 fichiers** sur `db1.lab` qui prouvent l'exécution de chaque mécanisme.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier 1 (import_tasks) | `/tmp/lab30a-import.txt` (`step: import-static`) |
| Fichiers 2, 3, 4 (include_tasks loop) | `/tmp/lab30a-loop-1.txt`, `lab30a-loop-2.txt`, `lab30a-loop-3.txt` |
| Permissions | `0644`, owner `root` |
| Mécanismes utilisés | **`ansible.builtin.import_tasks`** + **`ansible.builtin.include_tasks`** avec `loop:` |

## 🧩 Bloqué ?

```bash
dsoxlab hint ecrire-code-import-include
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/import-include/challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/import-include/challenge/tests/
```

Le test pytest valide :

- `/tmp/lab30a-import.txt` existe + contient `import-static`.
- `/tmp/lab30a-loop-1.txt`, `-2.txt`, `-3.txt` existent + contiennent `iteration: <N>`.
- Le playbook utilise bien `import_tasks` ET `include_tasks` (pas un mix).

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-import-include
```

## 💡 Pour aller plus loin

- **`apply:`** sur `include_tasks` : injecter `tags`/`become`/`when` à toutes les tâches **internes** au fichier inclus.
- **`import_playbook`** : niveau **plays**, pour orchestrer plusieurs playbooks. Pas utilisable dans `tasks:`.
- **`include_role` + `loop:`** : pattern avancé pour appliquer un rôle plusieurs fois avec différentes vars.

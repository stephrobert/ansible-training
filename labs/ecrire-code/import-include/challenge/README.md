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

## 🧩 Indices

### Étape 1 — Fichiers de tâches

Créer dans `labs/ecrire-code/import-include/challenge/tasks/` :

`tasks/static.yml` :

```yaml
---
- name: Marker static (import_tasks)
  ansible.builtin.copy:
    dest: ???                    # ← /tmp/lab30a-import.txt
    content: ???
    mode: ???
```

`tasks/loop.yml` :

```yaml
---
- name: Marker loop (include_tasks dynamic)
  ansible.builtin.copy:
    dest: "/tmp/lab30a-loop-{{ item }}.txt"
    content: "iteration: {{ item }}\n"
    mode: ???
```

### Étape 2 — Squelette `solution.yml`

```yaml
---
- name: Challenge 30a — import + include + loop
  hosts: ???
  become: ???
  gather_facts: false

  tasks:
    - name: Static — import_tasks (parsé au start)
      ansible.builtin.???: ???        # ← import_tasks, fichier static.yml

    - name: Dynamic — include_tasks dans une loop
      ansible.builtin.???: ???        # ← include_tasks (loop NE marche PAS avec import_tasks)
      loop: ???                        # ← [1, 2, 3]
```

> 💡 **Pièges** :
> - **`import_tasks` ne supporte PAS `loop:`** car résolu au démarrage avant que `item` n'existe. Utiliser **`include_tasks`** pour boucler.
> - **FQCN obligatoire** : `ansible.builtin.import_tasks`, pas juste `import_tasks` (règle `fqcn-builtins` d'ansible-lint).
> - Le **chemin des `tasks/*.yml`** est relatif au playbook. Avec `solution.yml` dans `challenge/`, le chemin est `tasks/static.yml` (pas `challenge/tasks/...`).

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
make -C labs/ecrire-code/import-include/ clean
```

## 💡 Pour aller plus loin

- **`apply:`** sur `include_tasks` : injecter `tags`/`become`/`when` à toutes les tâches **internes** au fichier inclus.
- **`import_playbook`** : niveau **plays**, pour orchestrer plusieurs playbooks. Pas utilisable dans `tasks:`.
- **`include_role` + `loop:`** : pattern avancé pour appliquer un rôle plusieurs fois avec différentes vars.

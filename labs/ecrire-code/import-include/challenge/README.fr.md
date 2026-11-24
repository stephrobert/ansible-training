# « pourquoi mon tag ne s'applique pas aux tâches incluses ? »

## La situation

Le playbook a atteint quatre cents lignes, alors il a été découpé en fichiers
de tâches. Et là, les choses sont devenues étranges : les tags ont cessé de
sélectionner ce que tout le monde attendait, un fichier devait tourner une
fois par environnement et refusait catégoriquement de boucler, et
`--list-tasks` n'affichait plus que la moitié du plan. Rien n'est cassé.
Ansible a deux façons de tirer un fichier : l'une résolue avant le démarrage
du run, l'autre au fil de son déroulement. Et elles ne se comportent pas
pareil. Vous séparez les deux sur `db1.lab`, depuis **control-node.lab**.

Votre mission :

1. Tirer un ensemble de tâches figé en **statique**, parsé avant même que le
   play ne commence, et le voir apparaître dans le plan.
2. Tirer un second fichier en **dynamique**, une fois par élément d'une boucle,
   et découvrir pourquoi la forme statique en est tout simplement incapable.
3. Poser les bons chemins : un fichier de tâches se résout **relativement au
   playbook**, pas au répertoire où vous vous trouvez.
4. Prouver que les deux mécanismes ont tourné : le marqueur statique sur db1,
   plus un marqueur par itération.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/import-include/

## 🎯 Challenge — Combiner `import_tasks` + `include_tasks` + boucle

### ✅ Objectif

Écrire un playbook qui combine les **3 patterns** (`import_tasks` static + `include_tasks` avec `loop:` + 1 tâche à part) et dépose **4 fichiers** sur `db1.lab` qui prouvent l'exécution de chaque mécanisme.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier 1 (import_tasks) | `/tmp/lab30a-import.txt` (`step: import-static`) |
| Fichiers 2, 3, 4 (include_tasks loop) | `/tmp/lab30a-loop-1.txt`, `lab30a-loop-2.txt`, `lab30a-loop-3.txt` |
| Permissions | `0644`, owner `root` |
| Mécanismes utilisés | **`ansible.builtin.import_tasks`** + **`ansible.builtin.include_tasks`** avec `loop:` |

### 🧩 Bloqué ?

```bash
dsoxlab hint ecrire-code-import-include
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/import-include/challenge/solution.yml
```

### 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/import-include/challenge/tests/
```

Le test pytest valide :

- `/tmp/lab30a-import.txt` existe + contient `import-static`.
- `/tmp/lab30a-loop-1.txt`, `-2.txt`, `-3.txt` existent + contiennent `iteration: <N>`.
- Le playbook utilise bien `import_tasks` ET `include_tasks` (pas un mix).

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-import-include
```

### 💡 Pour aller plus loin

- **`apply:`** sur `include_tasks` : injecter `tags`/`become`/`when` à toutes les tâches **internes** au fichier inclus.
- **`import_playbook`** : niveau **plays**, pour orchestrer plusieurs playbooks. Pas utilisable dans `tasks:`.
- **`include_role` + `loop:`** : pattern avancé pour appliquer un rôle plusieurs fois avec différentes vars.

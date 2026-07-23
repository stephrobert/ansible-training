# 🎯 Challenge — Profiler 3 tâches sur `db1.lab`

## ✅ Objectif

Écrire un playbook qui exécute **3 tâches mesurables** sur `db1.lab`, activer le callback `profile_tasks`, et déposer un fichier `/tmp/lab89-profile.txt` qui contient les **noms** des 3 tâches dans l'ordre où elles ont été exécutées.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab89-profile.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | Les 3 noms de tâches séparés par `\n` (un par ligne) |
| Callbacks activés | `ansible.posix.profile_tasks` (visible dans la sortie) |

## 🧩 Bloqué ?

```bash
dsoxlab hint troubleshooting-verbosite
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

Depuis la racine du repo :

```bash
ANSIBLE_CONFIG=labs/troubleshooting/verbosite/ansible.cfg \
  ansible-playbook labs/troubleshooting/verbosite/challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/troubleshooting/verbosite/challenge/tests/
```

Le test pytest+testinfra valide :

- `/tmp/lab89-profile.txt` existe sur `db1.lab` avec mode `0644`.
- Le fichier contient **exactement 3 lignes** non vides (les 3 noms de tâches).
- L'`ansible.cfg` de niveau lab existe et active `ansible.posix.profile_tasks`
  (avec `callback_result_format = yaml`) : le callback qui est tout le sujet du lab.

## 🧹 Reset

```bash
dsoxlab clean troubleshooting-verbosite
```

## 💡 Pour aller plus loin

- **Plusieurs callbacks combinés** : ajouter `ansible.posix.timer` pour le temps total.
- **Capture de timing** : rediriger la sortie `ansible-playbook` vers un fichier, parser avec `grep -E 'TASK execution time'`.
- **`ansible-lint`** : `ansible-lint --profile production challenge/solution.yml` doit retourner vert.

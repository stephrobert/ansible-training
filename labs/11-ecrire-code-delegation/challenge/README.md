# 🎯 Challenge — `delegate_to` + `run_once` + marqueurs

## ✅ Objectif

Écrire `solution.yml` qui :

1. Cible le groupe `webservers` (web1, web2)
2. Pose un fichier marqueur **sur chaque webserver** via une tâche standard :
   `/tmp/delegation-on-{{ inventory_hostname }}.txt`
3. Pose **un seul** fichier sur **db1.lab** via `delegate_to: db1.lab` +
   `run_once: true` : `/tmp/delegation-on-db1.txt`

## 🧪 Validation

Le test pytest vérifie :

- `/tmp/delegation-on-web1.lab.txt` existe sur web1
- `/tmp/delegation-on-web2.lab.txt` existe sur web2
- `/tmp/delegation-on-db1.txt` existe sur **db1** (preuve `delegate_to`)
- Aucun fichier `/tmp/delegation-on-db1.txt` sur web1 ou web2

```bash
pytest -v labs/11-ecrire-code-delegation/challenge/tests/
```

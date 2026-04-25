# 🎯 Challenge — Job async qui pose un marqueur après 5 secondes

## ✅ Objectif

Écrire `solution.yml` qui sur **db1.lab** :

1. Lance en async (`async: 30, poll: 0`) un `shell` qui :
   - attend 5 secondes
   - pose `/tmp/async-done.txt` avec le contenu `Async OK`
2. Capture le job ID dans `register: async_job`
3. Attend la fin avec `async_status:` + `until: result.finished`

## 🧪 Validation

Le test pytest vérifie sur db1 :

- `/tmp/async-done.txt` existe et contient `Async OK`

```bash
pytest -v labs/10-ecrire-code-async-poll/challenge/tests/
```

# 🎯 Challenge — Job async qui pose un marqueur après 5 secondes

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** :

1. Lance **en async** une commande qui dort 5 secondes puis pose
   `/tmp/async-done.txt` avec le contenu `Async OK`.
2. Attend la fin du job sans bloquer le control node, via `async_status`.

## 🧩 Bloqué ?

```bash
dsoxlab hint ecrire-code-async-poll
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/async-poll/challenge/solution.yml
```

🔍 **Ce que vous devez voir** :

- La 1ère tâche (`Lancer le job`) retourne **immédiatement** (`poll: 0`).
- La 2ème tâche (`async_status`) **boucle** jusqu'à ce que `result.finished == 1`.
- Le `PLAY RECAP` final : `ok=2, changed=1`.

Vérifiez le fichier sur db1 :

```bash
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/async-done.txt"
# Doit afficher : Async OK
```

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/async-poll/challenge/tests/
```

Le test vérifie sur db1 :

- `/tmp/async-done.txt` existe.
- Son contenu inclut `Async OK`.

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-async-poll
```

## 💡 Pour aller plus loin

- **`async: 0`** : équivaut à un run synchrone classique (l'inverse d'async).
- **Job qui dépasse le timeout** : posez `async: 3` sur un `sleep 5` et observez
  l'erreur `'rc': -1, 'msg': 'Timeout'` — le job est **tué** par Ansible.
- **`fire-and-forget` complet** : sans `async_status`, le job tourne en
  arrière-plan et le play se termine sans attendre. Utile pour des jobs très
  longs (backups, indexations) où on ne veut pas que Ansible bloque.
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/async-poll/challenge/solution.yml
   ```

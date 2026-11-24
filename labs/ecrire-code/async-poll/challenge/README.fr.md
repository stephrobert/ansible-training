# La session SSH meurt avant le job

## La situation

Le job de maintenance nocturne de **db1.lab** dure vingt minutes. Le playbook
qui le lance échoue vers la dixième minute, à chaque fois, sur un tuyau SSH
rompu. Pire : personne ne sait dire si le job est mort avec la connexion ou
s'il continue de tourner sur l'hôte. Maintenir une session SSH ouverte pendant
toute la durée d'une tâche longue n'est pas une stratégie. Ansible a une vraie
réponse : lancer, lâcher, et revenir chercher le résultat.

Vous répétez le pattern depuis **control-node.lab** sur un job volontairement
court.

Votre mission :

1. Lancer une tâche longue sur `db1.lab` **en arrière-plan** et récupérer la
   main immédiatement, sans attendre sa fin.
2. Conserver son **job id** : une tâche lancée sans jamais être vérifiée est
   une tâche dont vous ne verrez jamais l'échec.
3. Interroger ce job avec **`async_status`** jusqu'à ce qu'il se déclare
   terminé, avec assez de tentatives et de délai pour couvrir sa durée réelle.
4. Prouver qu'elle a abouti : le fichier marqueur existe sur `db1.lab` avec le
   contenu attendu, et le récapitulatif est cohérent.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/async-poll/

## 🎯 Challenge — Job async qui pose un marqueur après 5 secondes

### ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** :

1. Lance **en async** une commande qui dort 5 secondes puis pose
   `/tmp/async-done.txt` avec le contenu `Async OK`.
2. Attend la fin du job sans bloquer le control node, via `async_status`.

### 🧩 Bloqué ?

```bash
dsoxlab hint ecrire-code-async-poll
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

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

### 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/async-poll/challenge/tests/
```

Le test vérifie sur db1 :

- `/tmp/async-done.txt` existe.
- Son contenu inclut `Async OK`.

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-async-poll
```

### 💡 Pour aller plus loin

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

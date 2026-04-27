# 🎯 Challenge — Job async qui pose un marqueur après 5 secondes

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** :

1. Lance **en async** une commande qui dort 5 secondes puis pose
   `/tmp/async-done.txt` avec le contenu `Async OK`.
2. Attend la fin du job sans bloquer le control node, via `async_status`.

## 🧩 Indices

Le pattern Ansible pour un job long en arrière-plan :

```yaml
- name: Lancer le job asynchrone (fire-and-forget)
  ansible.builtin.shell: ???
  async: ???        # timeout total en secondes (ex: 30)
  poll: 0           # 0 = ne pas attendre, retourne immédiatement le job_id
  register: ???     # capture le job_id

- name: Attendre la fin du job
  ansible.builtin.async_status:
    jid: "{{ ???.ansible_job_id }}"
  register: ???
  until: ???.finished
  retries: ???
  delay: ???
```

À compléter :

- La commande `shell:` doit faire `sleep 5` puis `echo "Async OK" > /tmp/async-done.txt`.
- Comme `shell:` n'est pas idempotent en lecture, ajoutez `changed_when: true`
  pour que le tag `changed` soit cohérent.
- Pour `async_status`, choisissez `retries` et `delay` qui couvrent les 5s
  d'attente (ex : `retries: 15, delay: 2`).

> 💡 **Pièges** :
>
> - **`async: 0` et `poll: 0`** : tâche fire-and-forget. Sans
>   `async_status:` derrière, vous ne savez **jamais** si elle a réussi.
> - **`async: N, poll: > 0`** : Ansible attend la fin (équivalent `poll:` sec
>   d'attente max), mais le SSH reste ouvert — pas vraiment async.
> - **`async: N, poll: 0` + `async_status:`** : le pattern correct.
>   Tâche lancée en background, on poll le job ID séparément.
> - **`retries × delay >= async`** : sinon `async_status` abandonne avant
>   la fin de la tâche. Pour `async: 5`, `retries: 15, delay: 2` (= 30 s
>   max) couvre largement.
> - **Job ID dans `register:`** : c'est `<var>.ansible_job_id` qu'il faut
>   passer à `async_status:`, pas l'objet entier.

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
make -C labs/ecrire-code/async-poll clean
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

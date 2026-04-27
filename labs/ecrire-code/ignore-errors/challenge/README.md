# 🎯 Challenge — Continuer après une erreur ignorée

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** :

1. Tente d'**arrêter un service inexistant** — la tâche échoue.
2. **Ignore l'erreur** explicitement.
3. Pose ensuite `/tmp/ignore-after.txt` contenant `play continued` — preuve
   que le play a continué malgré l'échec.

Le play termine en succès (`failed=0`) malgré l'erreur silencieuse.

## 🧩 Indices

- **`ignore_errors: true`** sur une tâche : l'erreur est loguée mais le play
  continue.
- **`ansible.builtin.systemd_service`** avec `state: stopped` sur un service
  qui n'existe pas → erreur garantie.

## 🧩 Squelette

```yaml
---
- name: Challenge - ignore_errors continue le play
  hosts: ???
  become: ???

  tasks:
    - name: Stopper un service qui n'existe pas
      ansible.builtin.systemd_service:
        name: ce-service-nexiste-pas
        state: stopped
      ignore_errors: ???

    - name: Marqueur post-échec ignoré
      ansible.builtin.copy:
        dest: ???                       # /tmp/ignore-after.txt
        content: ???                    # "play continued"
        mode: "0644"
```

> 💡 **Pièges** :
>
> - **`ignore_errors` ≠ `ignore_unreachable`** : le premier ignore les
>   échecs de tâche, le second les hôtes injoignables. À l'examen, lire
>   attentivement quel type d'erreur la consigne demande d'ignorer.
> - **`ignore_errors: true`** est un **keyword task-level**, pas un
>   paramètre du module. Le placer dans `systemd_service:` donne une
>   erreur "Unsupported parameters".
> - **Anti-pattern** : `ignore_errors: true` sur une tâche **critique**
>   masque un vrai problème. Toujours combiner avec `register:` + `when:`
>   pour réagir au lieu de simplement ignorer.
> - **Lecture du `PLAY RECAP`** : `failed=0, ignored=1` — la colonne
>   `ignored` n'existe pas dans toutes les versions, mais le compteur
>   d'erreurs ne s'incrémente pas avec `ignore_errors`.

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/ignore-errors/challenge/solution.yml
```

🔍 **Sortie attendue** :

- 1ère tâche : `failed!` mais `...ignoring`
- 2ème tâche : `changed`
- `PLAY RECAP` : `failed=0, ignored=1`

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/ignore-errors/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ecrire-code/ignore-errors clean
```

## 💡 Pour aller plus loin

- **`ignore_unreachable: true`** : continue même si l'hôte devient
  injoignable (différent d'`ignore_errors` qui ne couvre que les **task
  failures**).
- **`ignore_errors` vs `failed_when: false`** : équivalents en pratique pour
  marquer un échec comme non bloquant. Préférez `failed_when: ...` si vous
  voulez conditionner.
- **Combiner avec `register:`** : capturez le résultat pour réagir plus loin
  via `when: previous_task is failed`.
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/ignore-errors/challenge/solution.yml
   ```

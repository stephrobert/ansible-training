# 🎯 Challenge — `block` + `rescue` + `always` sur erreur volontaire

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** :

1. Lance dans un `block:` une commande **qui échoue volontairement**.
2. Capture l'échec dans `rescue:` qui pose `/tmp/challenge-rescue.txt` avec le
   contenu `rescue triggered (block failed)`.
3. Pose **toujours** `/tmp/challenge-always.txt` avec `always executed` dans
   `always:`.
4. Le `PLAY RECAP` final doit afficher **`failed=0`** — le rescue a rattrapé
   l'erreur et le play termine en **succès**.

## 🧩 Pattern

```yaml
- name: Bloc transactionnel
  block:
    - <tâche qui peut échouer>
  rescue:
    - <tâche exécutée si une tâche du block a échoué>
  always:
    - <tâche toujours exécutée, succès ou échec>
```

Analogie Python : `try / except / finally`.

## 🧩 Squelette

```yaml
---
- name: Challenge - block / rescue / always
  hosts: db1.lab
  become: true

  tasks:
    - name: Bloc avec rescue + always
      block:
        - name: Tâche qui échoue volontairement
          ansible.builtin.command: ???    # commande qui retourne rc != 0
          changed_when: false             # cmd qui ne modifie pas l'état réel

      rescue:
        - name: Marqueur rescue (capté)
          ansible.builtin.copy:
            dest: ???
            content: ???
            mode: "0644"

      always:
        - name: Marqueur always
          ansible.builtin.copy:
            dest: ???
            content: ???
            mode: "0644"
```

> 💡 **Indice commande qui échoue** : `/bin/false` retourne toujours rc=1. Vous
> pouvez aussi utiliser `command: /bin/sh -c 'exit 1'`.

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/block-rescue-always/challenge/solution.yml
```

🔍 **Sortie attendue** :

- `TASK [Tâche qui échoue volontairement]` → `FAILED!`
- `TASK [Marqueur rescue]` → `changed`
- `TASK [Marqueur always]` → `changed`
- `PLAY RECAP` : `failed=0` (le rescue a rattrapé)

> 💡 **Pièges** :
>
> - **`block:` + `rescue:` + `always:`** : structure try/except/finally
>   d'Ansible. `rescue` ne tourne que si une tâche du `block` échoue.
>   `always` tourne **toujours**, succès ou échec.
> - **`ignore_errors:` dans un `block`** : ignore l'erreur ET ne déclenche
>   pas le `rescue`. À utiliser avec parcimonie — préférer `rescue` qui
>   est plus explicite.
> - **`failed_when:` au niveau d'une tâche** : permet de **forcer** un
>   échec sur une condition custom. Combiné avec `block`, ça donne un
>   contrôle fin du flux.
> - **Variables disponibles dans `rescue`** : `ansible_failed_task` et
>   `ansible_failed_result` pour debug. Ne pas les confondre avec
>   `ansible_failed_handler` (handlers échoués).

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/block-rescue-always/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ecrire-code/block-rescue-always clean
```

## 💡 Pour aller plus loin

- **`ansible_failed_task` / `ansible_failed_result`** : variables magiques
  disponibles dans `rescue:` qui exposent la tâche qui a échoué et son
  résultat. Utile pour logger ou notifier.
- **Blocks imbriqués** : un `block:` peut contenir un autre `block:` avec son
  propre `rescue:`. Pattern de fallback en cascade.
- **Différence avec `ignore_errors`** (lab 25) : `ignore_errors` ignore
  silencieusement l'échec ; `block/rescue` permet une **action de
  rattrapage** explicite (rollback, log, notification).
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/block-rescue-always/challenge/solution.yml
   ```

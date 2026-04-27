# 🎯 Challenge — `wait_for:` + `pause:` (synchronisation)

## ✅ Objectif

Sur **db1.lab**, écrire un play qui :

1. Lance en arrière-plan une commande qui crée `/tmp/lab-waitfor-marker.txt`
   après **3 secondes**.
2. Utilise `wait_for: path:` pour **attendre** que le fichier apparaisse
   (timeout 10s).
3. **Pause** de 1 seconde pour stabilisation.
4. Vérifie que **sshd** écoute sur le port **22** (TCP) via `wait_for: port:`
   — `chronyd`/323 est UDP, non testable par `wait_for: port:` qui teste **TCP uniquement**.
5. Écrit un fichier de **succès** `/tmp/lab-waitfor-success.txt`.

## 🧩 Étapes

```yaml
---
- name: Challenge - wait_for + pause
  hosts: db1.lab
  become: true

  tasks:
    - name: S assurer que chronyd tourne
      ansible.builtin.systemd_service:
        name: chronyd
        state: started

    - name: Lancer en arriere-plan une commande qui cree un marker dans 3s
      ansible.builtin.shell: |
        ( sleep 3 && touch /tmp/lab-waitfor-marker.txt ) &
        echo OK
      changed_when: false

    - name: Attendre que le marker apparaisse
      ansible.builtin.wait_for:
        path: ???
        timeout: ???

    - name: Pause 1 seconde pour stabilisation
      ansible.builtin.pause:
        seconds: ???

    - name: Verifier que chronyd ecoute sur 323/udp (en realite TCP/UDP)
      ansible.builtin.wait_for:
        port: ???
        host: ???
        timeout: 5

    - name: Marker - succes
      ansible.builtin.copy:
        content: "Synchronisation OK : marker + port chronyd actifs.\n"
        dest: ???
        mode: "0644"
```

> 💡 **Pièges** :
>
> - **`wait_for: port: 123`** : attend un port en LISTEN. **`state:
>   started`** = port ouvert ; **`state: stopped`** = port fermé.
> - **`timeout:`** par défaut 300s. Pour des services lents (DB, LDAP),
>   augmenter à 600+. Pour un test rapide, baisser à 30 — sinon attente
>   inutile en cas d'échec.
> - **`pause:`** est **bloquant** côté control node (pas le managed
>   node). Utiliser **`wait_for:`** chaque fois que possible (event-driven
>   au lieu de timer aveugle).
> - **`wait_for: path: ...`** : attend qu'un fichier existe. Combiné
>   avec `delay:`, utile pour synchroniser avec un service qui pose
>   un marqueur.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-diagnostic/wait-for-pause/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "ls /tmp/lab-waitfor-*"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-diagnostic/wait-for-pause/challenge/tests/
```

## 🧹 Reset

```bash
ansible db1.lab -b -m shell -a "rm -f /tmp/lab-waitfor-*"
```

## 💡 Pour aller plus loin

- **`active_connection_states:`** sur `wait_for: port:` : matcher les états
  TCP précis (`LISTEN` uniquement).
- **`delay:` + `sleep:`** : pour des services **lents** à démarrer.
- **Pattern `uri: + until:` (lab 50)** : test **applicatif** (HTTP 200 + body
  OK), pas juste port TCP.
- **`pause: prompt:`** : confirmation interactive — bloque le play en
  attendant ENTRE de l'opérateur.
- **Lint** :

   ```bash
   ansible-lint labs/modules-diagnostic/wait-for-pause/challenge/solution.yml
   ```

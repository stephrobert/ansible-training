# Replace the blind sleeps holding the deployment together

## The situation

The deployment playbook for **db1.lab** is riddled with `sleep 30`, each one
added the day something went wrong. Nobody dares remove them, and they still are
not enough: the job sometimes finishes in two seconds, sometimes in forty, and
the play carries on regardless of what actually happened. Waiting blindly is not
synchronizing. You rewrite the sequence from **control-node.lab** so it waits for
**events**, not for the clock.

Your mission:

1. On **db1.lab**, launch the background job that lays down its marker after a
   few seconds, then **wait for the marker to appear** with a timeout that
   fails fast instead of hanging for minutes.
2. Add a short **stabilization pause**, the one case where a timer is honest,
   and know that it blocks the control node, not the managed node.
3. **Check the service is actually listening** on its port before declaring
   success: a service that is `started` is not always a service that answers,
   and the module only tests TCP.
4. Write the success marker once, and only once, the synchronization holds.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-wait-for-pause/ (in French)

## 🎯 Challenge — `wait_for:` + `pause:` (synchronization)

### ✅ Objective

On **db1.lab**, write a play that:

1. Launches in the background a command that creates
   `/tmp/lab-waitfor-marker.txt` after **3 seconds**.
2. Uses `wait_for: path:` to **wait** for the file to appear (timeout 10s).
3. **Pauses** for 1 second for stabilization.
4. Checks that **sshd** listens on port **22** (TCP) via `wait_for: port:`,
   `chronyd`/323 is UDP, not testable by `wait_for: port:` which tests **TCP only**.
5. Writes a **success** file `/tmp/lab-waitfor-success.txt`.

### 🧩 Steps

```yaml
---
- name: Challenge - wait_for + pause
  hosts: db1.lab
  become: true

  tasks:
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

    - name: Verifier que sshd ecoute sur 22/TCP
      ansible.builtin.wait_for:
        port: ???                          # 22
        host: ???                          # 127.0.0.1
        timeout: 5

    - name: Marker - succes
      ansible.builtin.copy:
        content: "Synchronisation OK : marqueur pose et port 22/TCP en ecoute.\n"
        dest: ???
        mode: "0644"
```

> 💡 **Traps**:
>
> - **`wait_for: port: 123`**: waits for a port in LISTEN. **`state:
>   started`** = port open; **`state: stopped`** = port closed.
> - **`timeout:`** default 300s. For slow services (DB, LDAP),
>   increase to 600+. For a quick test, lower to 30, otherwise a
>   useless wait in case of failure.
> - **`pause:`** is **blocking** on the control node side (not the managed
>   node). Use **`wait_for:`** whenever possible (event-driven
>   instead of a blind timer).
> - **`wait_for: path: ...`**: waits for a file to exist. Combined
>   with `delay:`, useful to synchronize with a service that drops
>   a marker.

### 🚀 Run

```bash
ansible-playbook labs/modules-diagnostic/wait-for-pause/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "ls /tmp/lab-waitfor-*"
```

### 🧪 Automated validation

```bash
pytest -v labs/modules-diagnostic/wait-for-pause/challenge/tests/
```

### 🧹 Reset

```bash
ansible db1.lab -b -m shell -a "rm -f /tmp/lab-waitfor-*"
```

### 💡 Going further

- **`active_connection_states:`** on `wait_for: port:`: match the precise TCP
  states (`LISTEN` only).
- **`delay:` + `sleep:`**: for services that are **slow** to start.
- **`uri: + until:` pattern (lab 50)**: **application** test (HTTP 200 + body
  OK), not just the TCP port.
- **`pause: prompt:`**: interactive confirmation, blocks the play while waiting
  for the operator's ENTER.
- **Lint**:

   ```bash
   ansible-lint labs/modules-diagnostic/wait-for-pause/challenge/solution.yml
   ```

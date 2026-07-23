# 🎯 Challenge — Two handlers, one task, and flush_handlers

You have written a task that notifies a handler. The challenge is to
trigger **two handlers from a single task** and force their **immediate**
execution via `meta: flush_handlers` to test the new config within
the same play.

## ✅ Objective

Write `solution.yml` that:

1. Targets `db1.lab`
2. Installs `nginx`, starts it, enables it
3. Modifies `/etc/nginx/nginx.conf` to set **`server_tokens off;`** AND
   **`add_header X-Content-Type-Options "nosniff";`** in the `http` block, via
   **two `lineinfile` tasks**

   > **Pedagogical note**: `server_tokens off;` alone does what Apache
   > required in two directives (`ServerTokens Prod` + `ServerSignature
   > Off`): it removes the version from the `Server` header **and** from the
   > error-page signature. The second hardening is therefore another point of the
   > pentest report, the `nosniff` header.
   >
   > Here, unlike `httpd.conf`, the `validate: nginx -t -c %s` directive
   > **works**: `nginx.conf` is self-contained (its `include` are absolute
   > paths), so nginx can validate the temporary file that `%s` passes to it.
   > Use it on both tasks.
4. The **first task** (`server_tokens`) notifies **two handlers**:
   `Reload nginx` AND `Notifier journal local` (a log file)
5. The **second task** (`add_header`) notifies only `Reload nginx`
6. After the two modifications, force the handlers to trigger via
   **`meta: flush_handlers`**
7. **Tests** the effect via `uri:` that calls `http://localhost` and captures
   the `Server` header

Skeleton of the handlers:

```yaml
handlers:
  - name: Reload nginx
    ansible.builtin.systemd:
      name: ???
      state: ???              # reloaded ≠ restarted, choose the least disruptive

  - name: Notifier journal local
    ansible.builtin.lineinfile:
      path: /var/log/ansible-handlers.log
      line: "Config nginx modifiée le {{ ??? }}"   # magic fact: ISO 8601 timestamp
      create: ???
      mode: "0644"
```

> 💡 **Pitfalls**:
>
> - `state: reloaded` reloads the config without killing the active connections
>   (preferable to `restarted` for nginx).
> - Both directives go in the `http { ... }` block: remember
>   `insertafter:` so you do not write them outside, where nginx would reject them.
> - The magic timestamp fact is in `ansible_date_time`, look for the
>   sub-key that gives the ISO 8601 format.
> - `create: true` is necessary for the **first** run (the log file
>   does not exist yet).

## 🧩 Instructions

1. Create `challenge/solution.yml`.
2. Run:

   ```bash
   ansible-playbook labs/ecrire-code/handlers/challenge/solution.yml
   ```

3. On the **first run**, you see the **two handlers** run (notified by
   the two tasks).
4. On the **second run**, **no handler** runs (`changed=0`).

## 🧪 Validation

The `tests/test_functional.py` script automatically checks on **db1.lab**:

- `nginx` is installed, running, enabled
- `/etc/nginx/nginx.conf` contains `server_tokens off;`
- `/etc/nginx/nginx.conf` contains an `add_header X-Content-Type-Options`
- The log file `/var/log/ansible-handlers.log` exists and contains an
  entry, proof that the **second handler** did trigger
- The HTTP request to `db1.lab` returns **200**
- The **Server header** in the HTTP response is exactly **`nginx`**
  (without version), proof that `server_tokens off;` is applied (the reload
  handler did run)
- The response carries **`X-Content-Type-Options: nosniff`**, same proof for the
  second task: the directive in the file is not enough, the reload must have happened

```bash
pytest -v labs/ecrire-code/handlers/challenge/tests/
```

## 🚀 Going further

- Redo the challenge using **`listen:`** on a
  `nginx-config-changed` topic. Both tasks notify this topic, and both
  handlers listen to it. Identical output, more decoupled code.
- Deliberately cause a **syntax error** in `nginx.conf`
  (for example `server_tokens Garbage;`). The `validate:` must prevent
  writing the file AND the handler must **not** be notified. On nginx
  this exercise really works, whereas it was impossible on `httpd.conf`.

---

Good luck! 🧠

## 🧹 Reset

To replay the challenge in a neutral state:

```bash
dsoxlab clean ecrire-code-handlers
```

This target uninstalls/removes what the solution placed on the managed
nodes (packages, files, services, firewall rules) so that you can
re-run the solution from scratch.

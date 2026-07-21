# 🎯 Challenge — Async job that lays down a marker after 5 seconds

## ✅ Objective

Write `challenge/solution.yml` that, on **db1.lab**:

1. Launches **in async** a command that sleeps 5 seconds then lays down
   `/tmp/async-done.txt` with the content `Async OK`.
2. Waits for the end of the job without blocking the control node, via `async_status`.

## 🧩 Hints

The Ansible pattern for a long background job:

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

To complete:

- The `shell:` command must do `sleep 5` then `echo "Async OK" > /tmp/async-done.txt`.
- Since `shell:` is not idempotent when reading, add `changed_when: true`
  so that the `changed` tag is coherent.
- For `async_status`, choose `retries` and `delay` that cover the 5s
  wait (e.g.: `retries: 15, delay: 2`).

> 💡 **Traps**:
>
> - **`async: 0` and `poll: 0`**: fire-and-forget task. Without
>   `async_status:` after it, you **never** know whether it succeeded.
> - **`async: N, poll: > 0`**: Ansible waits for the end (equivalent to `poll:` sec
>   of max wait), but SSH stays open: not really async.
> - **`async: N, poll: 0` + `async_status:`**: the correct pattern.
>   Task launched in the background, we poll the job ID separately.
> - **`retries × delay >= async`**: otherwise `async_status` gives up before
>   the end of the task. For `async: 5`, `retries: 15, delay: 2` (= 30 s
>   max) covers it widely.
> - **Job ID in `register:`**: it is `<var>.ansible_job_id` that must be
>   passed to `async_status:`, not the whole object.

## 🚀 Launch

```bash
ansible-playbook labs/ecrire-code/async-poll/challenge/solution.yml
```

🔍 **What you should see**:

- The 1st task (`Lancer le job`) returns **immediately** (`poll: 0`).
- The 2nd task (`async_status`) **loops** until `result.finished == 1`.
- The final `PLAY RECAP`: `ok=2, changed=1`.

Check the file on db1:

```bash
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/async-done.txt"
# Doit afficher : Async OK
```

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/async-poll/challenge/tests/
```

The test checks on db1:

- `/tmp/async-done.txt` exists.
- Its content includes `Async OK`.

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-async-poll
```

## 💡 Going further

- **`async: 0`**: equivalent to a classic synchronous run (the opposite of async).
- **Job that exceeds the timeout**: set `async: 3` on a `sleep 5` and observe
  the error `'rc': -1, 'msg': 'Timeout'`: the job is **killed** by Ansible.
- **Full `fire-and-forget`**: without `async_status`, the job runs in the
  background and the play ends without waiting. Useful for very
  long jobs (backups, indexing) where you do not want Ansible to block.
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/async-poll/challenge/solution.yml
   ```

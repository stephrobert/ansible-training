# 🎯 Challenge — Async job that lays down a marker after 5 seconds

## ✅ Objective

Write `challenge/solution.yml` that, on **db1.lab**:

1. Launches **in async** a command that sleeps 5 seconds then lays down
   `/tmp/async-done.txt` with the content `Async OK`.
2. Waits for the end of the job without blocking the control node, via `async_status`.

## 🧩 Stuck?

```bash
dsoxlab hint ecrire-code-async-poll
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

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

# The SSH session dies before the job does

## The situation

The nightly maintenance job on **db1.lab** takes twenty minutes. The playbook
that launches it fails around minute ten, every time, on a broken SSH pipe.
Worse: nobody can say whether the job died with the connection or is still
grinding away on the host. Holding an SSH session open for the whole duration
of a long task is not a plan. Ansible has a proper answer: launch it, let go,
and come back for the result.

You rehearse the pattern from **control-node.lab** on a deliberately short job.

Your mission:

1. Fire a long task on `db1.lab` **in the background** and get control back
   immediately, without waiting for it to end.
2. Keep its **job id**: a fire-and-forget task nobody ever checks is a task
   whose failure you will never see.
3. Poll that job with **`async_status`** until it reports finished, with enough
   retries and delay to actually cover the run time.
4. Prove it landed: the marker file exists on `db1.lab` with the expected
   content, and the recap is coherent.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/async-poll/ (in French)

## 🎯 Challenge — Async job that lays down a marker after 5 seconds

### ✅ Objective

Write `challenge/solution.yml` that, on **db1.lab**:

1. Launches **in async** a command that sleeps 5 seconds then lays down
   `/tmp/async-done.txt` with the content `Async OK`.
2. Waits for the end of the job without blocking the control node, via `async_status`.

### 🧩 Stuck?

```bash
dsoxlab hint ecrire-code-async-poll
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

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

### 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/async-poll/challenge/tests/
```

The test checks on db1:

- `/tmp/async-done.txt` exists.
- Its content includes `Async OK`.

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-async-poll
```

### 💡 Going further

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

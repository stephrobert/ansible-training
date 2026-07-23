# 🎯 Challenge — `serial: 1` + `max_fail_percentage`

## ✅ Objective

Write `challenge/solution.yml` that lays down a marker file on **web1.lab and
web2.lab**, in that order guaranteed by `serial: 1`.

You must prove via the **mtimes** that `serial: 1` did sequentialize the
execution (web1 processed **completely** before web2 starts).

## 🧩 Stuck?

```bash
dsoxlab hint ecrire-code-parallelisme-strategies
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🚀 Run

```bash
ansible-playbook labs/ecrire-code/parallelisme-strategies/challenge/solution.yml
```

🔍 **What you must see** in the output:

- The `PLAY [...]` banner appears **twice**: once for web1, once
  for web2 (because `serial: 1` restarts the play at each batch).
- On each play, you see `Marqueur ...` then `Pause ...`.
- The final `PLAY RECAP` shows `changed=1` on **both** hosts (the marker;
  `pause` changes nothing).
- **Rerun the command**: the second `PLAY RECAP` must show `changed=0`
  everywhere. This is what `test_solution_idempotente` checks.

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/parallelisme-strategies/challenge/tests/
```

The test checks:

- The 2 files `/tmp/serial-web1.lab.txt` and `/tmp/serial-web2.lab.txt` exist.
- The **mtime** of the file on web1 is **strictly earlier** than the one on web2
  (mechanical proof of the sequentialization).
- The **second pass** of the playbook changes nothing (`changed=0`).

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-parallelisme-strategies
```

Removes the markers on the 2 webservers to replay the scenario from scratch.

## 💡 Going further

- **`strategy: free`**: add this keyword to the play and observe the difference,
  each host progresses at its own pace. To combine with `serial:` for mixed
  scenarios.
- **`max_fail_percentage: 30`**: tolerates up to 30% of hosts failing before
  stopping. Useful on groups of 20+ hosts.
- **Lint with `ansible-lint`**:

   ```bash
   ansible-lint labs/ecrire-code/parallelisme-strategies/challenge/solution.yml
   # Strict mode (production):
   ansible-lint --profile production \
       labs/ecrire-code/parallelisme-strategies/challenge/solution.yml
   ```

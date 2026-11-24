# Both webservers went down in the same second

## The situation

The last deployment took the site offline for ninety seconds. Nothing failed:
the playbook simply did its job on **web1.lab** and **web2.lab** in parallel
and restarted both at once. Behind a load balancer, two healthy nodes updated
simultaneously means zero nodes serving. The answer is not to slow everything
down, it is to tell Ansible to walk the fleet one host at a time and to stop
dead on the first failure rather than break the second node too. You fix it
from **control-node.lab**.

Your mission:

1. Target the `webservers` group and roll the play out **one host at a time**.
2. Set the tolerance to zero: the first failing host stops the play before it
   ever touches the next one.
3. Drop a **marker** on each host, and slow each batch just enough that the two
   modification times cannot collide. Keep the marker's contents stable across
   runs: its mtime is the witness, not what is written inside it.
4. Prove the sequencing instead of assuming it: web1's marker must be strictly
   older than web2's. Read the output too, the `PLAY` banner now appears once
   per batch, not once per run.
5. Replay the playbook with nothing changed: it must report no change at all.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/parallelisme-strategies/ (in French)

## 🎯 Challenge — `serial: 1` + `max_fail_percentage`

### ✅ Objective

Write `challenge/solution.yml` that lays down a marker file on **web1.lab and
web2.lab**, in that order guaranteed by `serial: 1`.

You must prove via the **mtimes** that `serial: 1` did sequentialize the
execution (web1 processed **completely** before web2 starts).

### 🧩 Stuck?

```bash
dsoxlab hint ecrire-code-parallelisme-strategies
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Run

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

### 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/parallelisme-strategies/challenge/tests/
```

The test checks:

- The 2 files `/tmp/serial-web1.lab.txt` and `/tmp/serial-web2.lab.txt` exist.
- The **mtime** of the file on web1 is **strictly earlier** than the one on web2
  (mechanical proof of the sequentialization).
- The **second pass** of the playbook changes nothing (`changed=0`).

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-parallelisme-strategies
```

Removes the markers on the 2 webservers to replay the scenario from scratch.

### 💡 Going further

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

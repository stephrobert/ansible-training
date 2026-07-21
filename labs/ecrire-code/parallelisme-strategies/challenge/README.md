# 🎯 Challenge — `serial: 1` + `max_fail_percentage`

## ✅ Objective

Write `challenge/solution.yml` that lays down a marker file on **web1.lab and
web2.lab**, in that order guaranteed by `serial: 1`.

You must prove via the **mtimes** that `serial: 1` did sequentialize the
execution (web1 processed **completely** before web2 starts).

## 🧩 Hints

- Target: group `webservers` (so 2 hosts web1 + web2).
- At the **play** level, enable two keywords:
  - `serial: 1` → one host at a time
  - `max_fail_percentage: 0` → immediate stop on the first error
- A task `ansible.builtin.copy` that lays down `/tmp/serial-{{ inventory_hostname }}.txt`.
  The content must be **stable** (for example `vague {{ inventory_hostname }}`):
  it is the **mtime** of the file that proves the sequentialization, never its content.
- A second task `ansible.builtin.pause` of 2 seconds so that the **mtime**
  of web1 is strictly earlier than the one of web2.

Skeleton to complete:

```yaml
---
- name: Challenge - serial 1 sur 2 webservers
  hosts: ???
  become: true
  serial: ???
  max_fail_percentage: ???

  tasks:
    - name: Marqueur de vague
      ansible.builtin.copy:
        dest: ???
        content: ???                   # STABLE content, see the trap below
        mode: "0644"

    - name: Pause pour que les mtimes soient distincts
      ansible.builtin.pause:
        seconds: ???
```

> 💡 **Traps**:
>
> - **`serial: 1`** = rolling 1-by-1 (slow, but safe). On 2 webservers,
>   the test `mtime web1 < web2` only passes if web1 is processed **before**
>   web2, not guaranteed by default. The pause helps to separate the mtimes.
> - **The marker content must be STABLE.** The temptation is to write
>   `{{ ansible_date_time.iso8601 }}` in it "to timestamp it". Two reasons not
>   to do it, and the second is fatal:
>
>   1. It proves nothing more. That fact carries the time of the **fact
>      collection**, not that of the file write. The `mtime`, itself, is laid
>      down by the kernel at the exact moment of the write: it is the only witness of
>      the wave. Worse, `ansible.cfg` caches the facts for 2 hours: the
>      same timestamp would be copied onto both hosts.
>   2. The content would change on every run, `copy:` would render **always
>      `changed`**, and `test_solution_idempotente` requires `changed=0` on the second
>      pass. Your playbook would fail.
> - **`strategy: linear`** (default) = play-blocking: all hosts
>   must finish a task before moving to the next. **`free`** =
>   each host progresses at its own pace, rare in production, useful in demo.
> - **`max_fail_percentage`**: tolerance beyond which the play
>   stops. Different from `any_errors_fatal` which is zero tolerance.
> - **`forks`** in `ansible.cfg` (default 5) limits the global parallelism.
>   With `serial: 10` but `forks: 5`, you process 5-by-5.

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

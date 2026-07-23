# 🎯 Challenge — `delegate_to` + `run_once`

## ✅ Objective

Write `challenge/solution.yml` that demonstrates **two** complementary mechanics:

1. **A standard task** iterates over all `webservers` (web1, web2) and places
   a **local** marker on each host: `/tmp/delegation-on-{{ inventory_hostname }}.txt`.
2. **A delegated task** places **a single** file on **db1.lab** (a host
   that is nonetheless absent from the `webservers` group): proof that `delegate_to`
   allows acting outside the pattern, and that `run_once` prevents the duplicate.

## 🧩 Stuck?

```bash
dsoxlab hint ecrire-code-delegation
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🚀 Launch

```bash
ansible-playbook labs/ecrire-code/delegation/challenge/solution.yml
```

🔍 **What you should see**:

- 1st task: `changed: [web1.lab]` and `changed: [web2.lab]` (two executions).
- 2nd task: **a single** line `changed: [web1.lab -> db1.lab]` (delegation
  notation: *what we target* → *where we act*). The `-> db1.lab` is crucial.

Verify:

```bash
# On the webservers (local markers)
ansible webservers -m ansible.builtin.command \
    -a "ls /tmp/delegation-on-*.txt"

# On db1 (delegated marker)
ansible db1.lab -m ansible.builtin.command \
    -a "ls /tmp/delegation-on-db1.txt"
```

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/delegation/challenge/tests/
```

The test checks:

- `/tmp/delegation-on-web1.lab.txt` on **web1**.
- `/tmp/delegation-on-web2.lab.txt` on **web2**.
- `/tmp/delegation-on-db1.txt` on **db1** (`delegate_to` proof).
- **No** `/tmp/delegation-on-db1.txt` on web1 or web2 (isolation proof).

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-delegation
```

## 💡 Going further

- **`delegate_facts: true`**: the facts collected on the delegated host are
  recorded on the target host (useful to share info from db1 to the
  webservers).
- **`local_action`** = `delegate_to: localhost`. Historical form still seen.
- **Load-balancer pattern**: before restarting a webserver, delegate to
  the LB host to drain it. After the restart, delegate again to
  re-inject it. Combined with `serial: 1` (lab 09), it is the classic rolling
  deploy.
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/delegation/challenge/solution.yml
   ```

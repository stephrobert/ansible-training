# One deployment record, not one per host

## The situation

Every rollout on **web1.lab** and **web2.lab** leaves a local trace on each
node, and that part works. The central record does not: the team wants **one**
line on **db1.lab** stating that the rollout happened. Today the playbook
writes it once per webserver, so db1 receives the same file twice in the same
second. On a forty-node fleet it would be forty times. And db1 is not even in
the `webservers` group.

You fix it from **control-node.lab**, without adding a second playbook.

Your mission:

1. From a play targeting `webservers`, drop a **local marker** on each host,
   named after the host itself.
2. Write the **central record on `db1.lab`** from that same play, even though
   db1 belongs to another group entirely.
3. Make sure that record is written **exactly once** for the whole batch, not
   once per webserver.
4. Read the `web1.lab -> db1.lab` notation in the output, then check the
   isolation: the central record exists on db1 and on neither webserver.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/delegation/ (in French)

## 🎯 Challenge — `delegate_to` + `run_once`

### ✅ Objective

Write `challenge/solution.yml` that demonstrates **two** complementary mechanics:

1. **A standard task** iterates over all `webservers` (web1, web2) and places
   a **local** marker on each host: `/tmp/delegation-on-{{ inventory_hostname }}.txt`.
2. **A delegated task** places **a single** file on **db1.lab** (a host
   that is nonetheless absent from the `webservers` group): proof that `delegate_to`
   allows acting outside the pattern, and that `run_once` prevents the duplicate.

### 🧩 Stuck?

```bash
dsoxlab hint ecrire-code-delegation
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

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

### 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/delegation/challenge/tests/
```

The test checks:

- `/tmp/delegation-on-web1.lab.txt` on **web1**.
- `/tmp/delegation-on-web2.lab.txt` on **web2**.
- `/tmp/delegation-on-db1.txt` on **db1** (`delegate_to` proof).
- **No** `/tmp/delegation-on-db1.txt` on web1 or web2 (isolation proof).

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-delegation
```

### 💡 Going further

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

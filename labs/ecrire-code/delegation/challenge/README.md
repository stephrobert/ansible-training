# 🎯 Challenge — `delegate_to` + `run_once`

## ✅ Objective

Write `challenge/solution.yml` that demonstrates **two** complementary mechanics:

1. **A standard task** iterates over all `webservers` (web1, web2) and places
   a **local** marker on each host: `/tmp/delegation-on-{{ inventory_hostname }}.txt`.
2. **A delegated task** places **a single** file on **db1.lab** (a host
   that is nonetheless absent from the `webservers` group): proof that `delegate_to`
   allows acting outside the pattern, and that `run_once` prevents the duplicate.

## 🧩 Hints

```yaml
---
- name: Challenge - delegation
  hosts: webservers
  become: true
  tasks:
    - name: Marqueur local sur chaque webserver
      ansible.builtin.copy:
        dest: ???        # interpolate inventory_hostname
        content: ???
        mode: "0644"

    - name: Marqueur centralisé sur db1 (déléguer + une seule fois)
      ansible.builtin.copy:
        dest: /tmp/delegation-on-db1.txt
        content: ???
        mode: "0644"
      delegate_to: ???
      run_once: ???
```

To complete:

- **`delegate_to: db1.lab`**: the task runs on db1, not on web1/web2.
- **`run_once: true`**: without it, the task would run twice (once per host of
  `webservers`), with the **same content** but on the **same** db1.lab → either
  useless or a conflict. `run_once` guarantees a single execution in the batch.

> 💡 **Traps**:
>
> - **`delegate_to:` does NOT change `inventory_hostname`**: the variable
>   stays that of the current play host. To get that of the
>   delegated target, use `delegate_facts: true` + `hostvars[delegate].…`.
> - **`run_once: true` without `delegate_to`**: the task runs on **the
>   first host** of the batch. Combined with `delegate_to: localhost`, it is
>   the "single task on the control node" pattern.
> - **`local_action:`**: shortcut for `delegate_to: localhost`. More
>   readable when you have only **a single** task to run locally.
> - **`become:` on a delegated task**: applies to **the delegated host**, not
>   to the play. `become: true` on a `delegate_to: localhost` task
>   requests sudo locally.

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

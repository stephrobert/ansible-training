# Lab 09 — Parallelism and strategies (`serial:`, `forks:`, `strategy:`)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root (see
> [root README](../../../README.md#-démarrage-rapide) for the details).

## 🧠 Recap

🔗 [**Ansible parallelism and strategies: forks, serial, throttle, strategy**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/parallelisme-strategies/)

By default, Ansible runs **one task at a time** on **`forks` hosts in parallel**
(default 5). `serial:` changes this behavior to **successive batches**, handy for
**rolling updates** (update 1 host, validate, move to the next). `strategy:`
changes the philosophy: `linear` (default) waits for all hosts to finish a task
before moving to the next; `free` lets each host progress independently.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Distinguish** `forks:` (global parallelism) from `serial:` (batch size).
2. **Run** a rolling update on the `webservers` with `serial: 1`.
3. **Compare** the `linear` (default) and `free` strategies on a realistic play.
4. **Limit** a single task with `throttle:` (targeted rate-limit without touching the play).
5. **Choose** the right `forks` / `serial` / `strategy` combination for the scenario.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible webservers -m ping
# Must list web1.lab and web2.lab as SUCCESS
```

Clean the markers from previous runs:

```bash
ansible webservers -b -m file -a "path=/tmp/serial-timestamp.txt state=absent"
ansible webservers -b -m file -a "path=/tmp/free-timestamp.txt state=absent"
```

## 📚 Exercise 1 — `serial: 1` (strict rolling update)

Create `lab.yml`:

```yaml
---
- name: Demo serial 1 sur webservers
  hosts: webservers
  become: true
  serial: 1
  tasks:
    - name: Marquer le timestamp
      ansible.builtin.shell: |
        date --iso-8601=ns > /tmp/serial-timestamp.txt
      changed_when: true

    - name: Pause realiste avant le suivant (2s)
      ansible.builtin.pause:
        seconds: 2
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/parallelisme-strategies/lab.yml
```

🔍 **Observation**: web1 processes its 2 tasks **completely** before web2 starts.
Check the timestamps:

```bash
ansible webservers -b -m command -a "cat /tmp/serial-timestamp.txt"
```

The timestamp of web2 must be **at least 2 seconds later** than the one of web1.
That is the point of `serial: 1`: if web1 crashes, web2 is never touched.

## 📚 Exercise 2 — `serial: ["20%", "50%"]` (progressive rolling)

On 2 hosts, `serial: ["20%", "50%"]` comes down to 1 then 1 (`max(1, 20% × 2)` = 1).
To demonstrate the pattern, we simulate 4 virtual hosts via `--limit` and the batch pattern.

Modify the play to add an explicit **second batch**:

```yaml
serial:
  - 1
  - "100%"  # All the remaining ones
```

🔍 **Observation**: Ansible displays `PLAY [Demo serial 1 sur webservers]` twice, once
for **batch 1** (web1 alone), once for **batch 2** (web2 alone, or all the others
if you had 10 hosts). The `serial: ["10%", "50%", "100%"]` is the classic pattern
of the **canary deploy**: 10% first (canary), 50% if OK, the rest at the end.

## 📚 Exercise 3 — `strategy: free` vs `linear`

Create `lab-strategy.yml`:

```yaml
---
- name: Demo strategy free
  hosts: webservers
  become: true
  strategy: free
  tasks:
    - name: Tache rapide (1s)
      ansible.builtin.pause:
        seconds: 1

    - name: Tache lente (5s)
      ansible.builtin.shell: |
        sleep 5
        date --iso-8601=ns > /tmp/free-timestamp.txt
      changed_when: true
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/parallelisme-strategies/lab-strategy.yml
```

🔍 **Observation**: with `strategy: free`, **each host progresses at its own pace**.
The `/tmp/free-timestamp.txt` timestamps on web1 and web2 are **close** (the hosts
started the slow task in parallel, not waiting for all to finish the fast one).

**Compare** with `strategy: linear` (default), change it to `strategy: linear`:

```bash
ansible-playbook labs/ecrire-code/parallelisme-strategies/lab-strategy.yml
```

🔍 **Observation**: in `linear`, Ansible **waits** for all hosts to finish the fast
task before launching the slow one. If a host is slower than the others (network,
load), the whole play is slowed down.

**Takeaway**: `linear` simplifies debugging and guarantees order. `free` maximizes
throughput but scrambles the logs.

## 📚 Exercise 4 — `throttle:` (targeted rate-limit)

You have a play over 50 hosts, `forks: 50`, but **a single task** calls an
external endpoint capped at 5 req/s. No need to put the whole play at `forks: 5`.

```yaml
- name: Tache qui appelle une API rate-limitee
  ansible.builtin.uri:
    url: https://api.example.com/register
    method: POST
  throttle: 5
```

`throttle: 5` limits **only this task** to 5 hosts in parallel, the rest of the
play continues at `forks: 50`.

🔍 **Observation**: `throttle:` is local to the task. No need to change the global
Ansible config.

## 📚 Exercise 5 — The trap: `serial:` + handlers

When `serial: 1` is in place, the **handlers** fire **per batch**, not at the
end of the global play. This can be surprising.

Create `lab-handlers.yml`:

```yaml
---
- name: Demo serial + handlers
  hosts: webservers
  become: true
  serial: 1
  tasks:
    - name: Modifier un fichier
      ansible.builtin.copy:
        content: "Modif au {{ ansible_date_time.iso8601 }}\n"
        dest: /tmp/lab-handler-trigger.txt
      notify: Recharger un service

  handlers:
    - name: Recharger un service
      ansible.builtin.debug:
        msg: "Handler tourne sur {{ inventory_hostname }} a {{ ansible_date_time.iso8601 }}"
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/parallelisme-strategies/lab-handlers.yml
```

🔍 **Observation**: the handler `Recharger un service` runs **2 times**: once
after web1 (end of batch 1), once after web2 (end of batch 2). In a **rolling update**,
this is exactly what you want (reload nginx on web1 before touching web2).
In **non-serial** mode, the handler would have run **only once** at the end on both hosts
in parallel.

## 🔍 Observations to note

- **`forks:`** = global parallelism (default 5, configurable in `ansible.cfg`).
- **`serial:`** = batch size, divides the play into sequential "waves".
- **`serial:` accepts a list** (`[1, 5, "100%"]`) for progressive batches (canary deploy).
- **`strategy: linear`** synchronizes the hosts task by task. **`strategy: free`** lets each one progress.
- **`throttle:`** rate-limits a precise task without touching the rest of the play.
- **Handlers + `serial:`** = handlers fired at the end of each batch (useful in rolling).

## 🤔 Reflection questions

1. You manage 100 webservers and you want to deploy a new nginx config with a
   **rolling update**, stopping if more than 5% fail. Which play options do you
   use? (combination of `serial:`, `max_fail_percentage:`, and strategy).

2. Why can `strategy: free` **speed up a play** on heterogeneous hosts
   (mix of slow / fast VMs), but **slow it down** on homogeneous hosts?

3. A colleague suggests putting `forks: 200` in `ansible.cfg` "to go faster".
   What are the **3 risks** you identify before accepting?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`max_fail_percentage:`**: tolerates a % of failures per batch before aborting. Combined
  with `serial:`, it is the **rolling with circuit-breaker** pattern.
- **`any_errors_fatal:`**: conversely, aborts on the first failure, see lab 25.
- **`run_once: true`**: run a task **only once** in a multi-host play
  (useful to notify an external load-balancer). See lab 11 (delegation).
- **Myth to bust**: raising `forks:` does **not multiply** the speed. Frequent
  bottleneck = the **fact gathering** on too many hosts in parallel saturates the control node.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/parallelisme-strategies/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/parallelisme-strategies/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/parallelisme-strategies/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.

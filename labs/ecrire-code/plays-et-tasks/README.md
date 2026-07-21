# Lab 05 — Plays and tasks (complete anatomy of a play)

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

🔗 [**Ansible plays and tasks: complete anatomy, execution order, keywords**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/plays-et-tasks/)

In lab 04, you wrote a simple play with just `tasks:`. But a real production play has **4 task sections** that execute in a precise order:

```text
gather_facts → pre_tasks → roles → tasks → post_tasks → handlers
```

Each section has its role:

- **`pre_tasks`**: preparations (snapshot, drain a load balancer, lay down a start marker).
- **`roles`**: factored and reusable code (seen later).
- **`tasks`**: the heart of the deployment.
- **`post_tasks`**: post-deployment checks (smoke test, end marker, notification).
- **`handlers`**: **reactive** tasks, triggered only if another task does `notify:` (lab 06).

> The **parallelism** keywords (`serial:`, `strategy:`, `max_fail_percentage:`) are **not** covered here, they are the subject of [lab 09: parallelism and strategies](../parallelisme-strategies/). Focus first on the **anatomy of a play**.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Write a structured play with **`pre_tasks` + `tasks` + `post_tasks` + `handlers`**.
2. Check the real **execution order** via timestamped marker files.
3. Distinguish a handler from a normal task.
4. Understand how `notify:` triggers a handler, and why an `ok` handler does not run.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible webservers -m ansible.builtin.ping
ansible webservers -b -m ansible.builtin.shell -a "rm -f /tmp/predeploy-* /tmp/postdeploy-*"
```

Expected response: 2 `pong`, then cleanup of the markers from a possible previous run.

## ⚙️ Target tree

```text
labs/ecrire-code/plays-et-tasks/
├── README.md           ← this file
├── playbook.yml        ← TO CREATE, your complete play
└── challenge/
    ├── README.md       ← final challenge (already present)
    └── tests/
        └── test_*.py   ← (already present, pytest+testinfra)
```

## 📚 Exercise 1 — Skeleton of the play

Create `labs/ecrire-code/plays-et-tasks/playbook.yml`:

```yaml
---
- name: Déployer nginx avec play complet (pre/tasks/post/handlers)
  hosts: webservers
  become: true

  pre_tasks:
    # You will write here: lay down a "predeploy" marker file

  tasks:
    # You will write here: install + start + configure nginx

  post_tasks:
    # You will write here: lay down a "postdeploy" marker file

  handlers:
    # You will write here: reload nginx
```

🔍 **Observation**: this play presents the **complete structure** of a professional deployment: preparations (`pre_tasks`), main action (`tasks`), validation (`post_tasks`), reactions to a change (`handlers`). The execution order is **guaranteed** by Ansible.

## 📚 Exercise 2 — `pre_tasks` ("predeploy" marker)

In `pre_tasks:`, create a marker file `/tmp/predeploy-{{ inventory_hostname }}.txt` via `ansible.builtin.copy` + `content:`. Hints:

- Module: `ansible.builtin.copy`
- `dest: "/tmp/predeploy-{{ inventory_hostname }}.txt"`
- `content: "predeploy {{ inventory_hostname }}\n"`
- `mode: "0644"`

🔍 **Observation to anticipate**: the content is **stable**, and that is the point. What will date this marker is its `mtime`, which the kernel lays down at the moment of the write. You will compare it to the one of the `postdeploy` marker in exercise 5.

> ⚠️ **The reflex not to acquire**: writing `content: "predeploy at {{ ansible_date_time.iso8601 }}"`. It is tempting, and it is wrong twice.
>
> - **It does not date the write.** `ansible_date_time` is a fact: it carries the time of the **fact collection**, not that of the task. And `ansible.cfg` caches the facts for 2 hours (`fact_caching_timeout`): from one run to another, and between `pre_tasks` and `post_tasks`, this fact is **frozen**. Your two markers would carry the same time.
> - **It breaks idempotence.** A content that changes on every run makes `copy:` render `changed` on every run. The role may well be "correct", but it lies about what it did.
>
> A timestamp in a `content:` is almost always the sign that you were looking for an `mtime`.

## 📚 Exercise 3 — `tasks` (nginx + firewalld opening)

In `tasks:`, chain 4 tasks:

1. **Install nginx**: `ansible.builtin.dnf` with `name: nginx`, `state: present`.
2. **Configure the welcome page**: `ansible.builtin.copy` that lays down `/etc/nginx/conf.d/site.conf` with a minimal `server` that serves `Hello world from {{ inventory_hostname }}`. This task **must notify** the handler, add `notify: Recharger nginx` at the end.
3. **Start + enable nginx**: `ansible.builtin.systemd` with `name: nginx`, `state: started`, `enabled: true`.
4. **Open HTTP in firewalld**: `ansible.posix.firewalld` with `service: http`, `permanent: true`, `immediate: true`, `state: enabled`.

🔍 **Observation to anticipate**: only task **(2)** notifies the handler, because it is the one that modifies the nginx config. The other 3 do not trigger a reload.

## 📚 Exercise 4 — `post_tasks` (smoke test + marker)

In `post_tasks:`, chain 2 tasks:

1. **Test** `http://localhost` with `ansible.builtin.uri`: `url: http://localhost`, `status_code: 200`.
2. **Lay down a marker** `/tmp/postdeploy-{{ inventory_hostname }}.txt` (same structure as the `predeploy` from exercise 2).

🔍 **Observation to anticipate**: `post_tasks` executes **after** the handlers from `tasks:` have run. This is exactly what we want for a smoke test: we test after the reload, not before.

## 📚 Exercise 5 — `handlers` (reload nginx)

In `handlers:`, add a single handler:

```yaml
- name: Recharger nginx
  ansible.builtin.systemd:
    name: nginx
    state: reloaded
```

🔍 **Observation to anticipate**: a handler looks like a normal task, but **only executes if a task does `notify:` it**. If the notifying task is `ok` (idempotent, nothing changed), the handler **does not run**. This is exactly the "restart-on-config-change" behavior, see lab 06 to go further.

## 📚 Exercise 6 — Run the playbook

From the repo root:

```bash
ansible-playbook labs/ecrire-code/plays-et-tasks/playbook.yml
```

🔍 **Observation**: Ansible plays **all the tasks** on **all the hosts** in the order `gather_facts → pre_tasks → tasks → handlers → post_tasks`. Without `serial:`, the hosts progress **in parallel** (by batch). The console output shows:

```text
PLAY [Déployer nginx ...] *********************************
TASK [Gathering Facts] ************************************
ok: [web1.lab]
ok: [web2.lab]
TASK [pre_tasks: predeploy] *******************************
changed: [web1.lab]
changed: [web2.lab]
... (all the tasks on all the hosts) ...
RUNNING HANDLER [Recharger nginx] *************************
changed: [web1.lab]
changed: [web2.lab]
TASK [post_tasks: smoke test] *****************************
ok: [web1.lab]
ok: [web2.lab]
```

> To process **one host at a time** (rolling update), there is the `serial:` keyword, it is the subject of [lab 09](../parallelisme-strategies/).

## 📚 Exercise 7 — Check the execution order

The marker files prove the order `pre_tasks` → `tasks` → `handlers` → `post_tasks`:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab 'sudo ls -la /tmp/predeploy-web1.lab.txt /tmp/postdeploy-web1.lab.txt'
```

🔍 **Observation**: the `mtime` of the `predeploy` file must be **strictly earlier** than the `mtime` of the `postdeploy` file. This is the proof that `pre_tasks` does execute before `post_tasks`, and notice where it comes from: from `ls -la`, not from the content of the files. Both markers carry an identical text on every run; it is their modification dates that testify. This is exactly what the challenge test compares.

## 📚 Exercise 8 — Check idempotence

Rerun:

```bash
ansible-playbook labs/ecrire-code/plays-et-tasks/playbook.yml
```

🔍 **Observation**: `PLAY RECAP` must display `changed=0` everywhere. And **important**: the handler `Recharger nginx` does not run (the `(2)` task is `ok`, no notification).

## 🔍 Observations to note

- Execution order **guaranteed**: `gather_facts` → `pre_tasks` (+ their handlers) → `roles` → `tasks` (+ their handlers) → `post_tasks` (+ their handlers).
- The **handlers** execute **at the end of their section** by default. To force them earlier: `meta: flush_handlers` (lab 06).
- A task is **`changed`** if it modified the state. A handler only triggers **on `changed`** (never on `ok`).
- The `notify:` on task `(2)` only triggers the handler **if the `site.conf` file really changed**. This is what makes the "restart-on-config-change" pattern idempotent.

## 🤔 Reflection questions

1. What happens if task **(2)** fails (invalid nginx config)? Is the handler triggered? Do the `post_tasks` run?

2. You want to **force** the nginx reload **before** the smoke test (without waiting for the end of `tasks:`). Which Ansible mechanism do you use? (Hint: `meta: flush_handlers`, lab 06.)

3. Why would the smoke test (`uri:` in `post_tasks`) run **before** the handler's reload if you had put it in `tasks:` instead of `post_tasks:`?

## 🚀 Final challenge

The challenge ([`challenge/README.md`](challenge/README.md)) reproduces the `pre_tasks` / `tasks` / `post_tasks` / `handlers` pattern on `db1.lab`, with nginx as in the tutorial: what changes is the host, not the software. Automated tests via `pytest+testinfra`:

```bash
pytest -v labs/ecrire-code/plays-et-tasks/challenge/tests/
```

## 💡 Going further

- **`meta: flush_handlers`**: force the immediate triggering of pending handlers, without waiting for the end of the section. See [lab 06: handlers](../handlers/).
- **Defensive `pre_tasks`**: a `pre_tasks` that calls an internal `/health` endpoint and fails **before** the slightest change, a classic pattern in production.
- **Parallelism and rolling updates**: `serial:`, `strategy:`, `max_fail_percentage:` are introduced in [lab 09](../parallelisme-strategies/).

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/plays-et-tasks/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/plays-et-tasks/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/plays-et-tasks/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.

# Lab 06 — Handlers (the restart-on-config-change pattern)

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

🔗 [**Ansible handlers: notify, listen, flush_handlers and restart-on-config-change**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/handlers/)

A **handler** is a **reactive task**: it runs **only if** another task has notified it **and** that task is `changed` (not `ok`). This is the pattern you will apply 100 times in production: "restart the service **only if** its config changed".

The 4 keywords to know:

| Keyword | Where | Role |
| --- | --- | --- |
| **`notify:`** | on a task | triggers a named handler (one or a list) |
| **`handlers:`** | dedicated section of the play | declares the handlers (same options as a task) |
| **`listen:`** | on a handler | groups several handlers under an abstract **topic** |
| **`meta: flush_handlers`** | special task | forces the **immediate** execution of pending handlers |

Without a handler, you write `state: restarted`, which restarts **on every run**, so it breaks idempotence. With a handler, you restart **only when necessary**.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Write a simple handler notified by a task.
2. Check that a handler **does not trigger** when its task is `ok` (idempotence).
3. Notify **several handlers** from a single task.
4. Use **`listen:`** to decouple tasks and handlers via a topic.
5. Force the immediate execution with **`meta: flush_handlers`**.
6. Combine **`validate:`** + a handler to **never** apply an invalid config.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible webservers -m ansible.builtin.ping
ansible webservers -b -m ansible.builtin.shell -a "rm -f /tmp/handler-*.txt"
```

Expected response: 2 `pong`. The second `ansible` cleans up any markers from a previous run.

## ⚙️ Target tree

```text
labs/ecrire-code/handlers/
├── README.md           ← this file
├── playbook.yml        ← TO CREATE, your play with handlers
└── challenge/
    ├── README.md       ← final challenge (already present)
    └── tests/
        └── test_*.py   ← (already present, pytest+testinfra)
```

## 📚 Exercise 1 — Play skeleton

Create `labs/ecrire-code/handlers/playbook.yml`:

```yaml
---
- name: Configurer nginx avec restart-on-config-change
  hosts: webservers
  become: true

  tasks:
    # Tasks that notify the handler

  handlers:
    # Handler that reloads nginx
```

🔍 **Observation**: `handlers:` is a **sibling section** of `tasks:` (at the same level, not inside it). Handlers never run on their own: a task must `notify:` them.

## 📚 Exercise 2 — First simple handler (notify)

In `tasks:`, add 3 tasks:

1. **Install nginx**: `ansible.builtin.dnf` with `name: nginx`, `state: present`.
2. **Start + enable nginx**: `ansible.builtin.systemd` with `name: nginx`, `state: started`, `enabled: true`.
3. **Modify `nginx.conf`**: `ansible.builtin.lineinfile` with:
   - `path: /etc/nginx/nginx.conf`
   - `regexp: '^\\s*server_tokens\\s+'`
   - `line: '    server_tokens off;'`
   - `insertafter: '^http\\s*\\{'` (the directive lives in the `http` block)
   - **`notify: Reload nginx`** ← the magic

In `handlers:`, add:

```yaml
- name: Reload nginx
  ansible.builtin.systemd:
    name: nginx
    state: reloaded
```

🔍 **Observation to anticipate**: task **(3)** notifies the `Reload nginx` handler. The `notify:` name must match the handler's `name:` **exactly**: case-sensitive, spaces included.

## 📚 Exercise 3 — Run and observe

From the root:

```bash
ansible-playbook labs/ecrire-code/handlers/playbook.yml
```

🔍 **Observation**, expected console output (excerpt):

```text
TASK [Modifier nginx.conf] *************************
changed: [web1.lab]                ← the task is "changed"
changed: [web2.lab]

RUNNING HANDLER [Reload nginx] *********************   ← the handler runs!
changed: [web1.lab]
changed: [web2.lab]

PLAY RECAP *****************************************
web1.lab    : ok=4    changed=2  ...
```

The `Reload nginx` handler ran **after** all the play's tasks. This is the **default behavior**: handlers are queued and **flushed at the end of their section**.

## 📚 Exercise 4 — Check that the handler **does not re-trigger**

Re-run the same command **immediately**:

```bash
ansible-playbook labs/ecrire-code/handlers/playbook.yml
```

🔍 **Observation**: this time, **no `RUNNING HANDLER` banner**. The `PLAY RECAP` shows `changed=0`. Why?

- Task **(3)** is `ok` (the line already complies).
- **No `changed` → no notification → no handler.**

This is exactly what we want: we **only reload nginx if the config really changed**. You have just seen the restart-on-config-change pattern applied.

## 📚 Exercise 5 — Check the effect of the reload

```bash
curl -s -I http://web1.lab | grep -i ^Server:
```

🔍 **Observation**: the `Server:` header must show `nginx` (without version): proof that `server_tokens off;` is applied **and** that nginx was indeed reloaded. Before the handler, you would have seen `nginx/1.26.x` (the default version).

> 💡 **Apache equivalence**: where Apache requires two directives (`ServerTokens Prod` for the header, `ServerSignature Off` for the error pages), nginx has only one. `server_tokens off;` hides the version **on both sides** at once.

## 📚 Exercise 6 — Notify **several handlers** from a task

`notify:` accepts a **list**. Modify task **(3)** to notify two handlers, and add the second one:

```yaml
- name: Modifier nginx.conf (server_tokens)
  ansible.builtin.lineinfile:
    path: /etc/nginx/nginx.conf
    regexp: '^\s*server_tokens\s+'
    line: '    server_tokens off;'
    insertafter: '^http\s*\{'
  notify:
    - Reload nginx
    - Notifier journal local
```

In `handlers:`, add the second one:

```yaml
- name: Notifier journal local
  ansible.builtin.lineinfile:
    path: /tmp/handler-journal.txt
    line: "Config nginx modifiée le {{ ansible_date_time.iso8601 }}"
    create: true
    mode: "0644"
```

> ⚠️ **Before re-running**, change the value of `line:` (e.g. `server_tokens on;`) to force a `changed`, otherwise the handlers will not trigger. Then re-run with the original value to restore the state.

🔍 **Observation**: when the task changes, **both handlers run**, in the order they are declared in `handlers:` (not in the order of the `notify:`).

## 📚 Exercise 7 — Decouple with `listen:` (topic)

`listen:` lets you listen to an **abstract topic** instead of a specific handler name. Handy to add a handler without touching the existing tasks.

Refactor exercise 6:

```yaml
tasks:
  - name: Modifier nginx.conf (server_tokens)
    ansible.builtin.lineinfile:
      path: /etc/nginx/nginx.conf
      regexp: '^\s*server_tokens\s+'
      line: '    server_tokens off;'
      insertafter: '^http\s*\{'
    notify: nginx-config-changed       # a topic, not a name

handlers:
  - name: Reload nginx
    listen: nginx-config-changed       # this handler listens to the topic
    ansible.builtin.systemd:
      name: nginx
      state: reloaded

  - name: Notifier journal local
    listen: nginx-config-changed       # this one too
    ansible.builtin.lineinfile:
      path: /tmp/handler-journal.txt
      line: "Config nginx modifiée le {{ ansible_date_time.iso8601 }}"
      create: true
      mode: "0644"
```

🔍 **Observation**: the task notifies **a single name** (`nginx-config-changed`), but **two handlers** trigger because they listen to this topic. If tomorrow you add a third handler on the same topic, **no task to modify**. That is the decoupling.

## 📚 Exercise 8 — Force immediate execution with `meta: flush_handlers`

By default, handlers run **at the end of the section** (`tasks` here). But sometimes you want to force them **before** a following task, typically to validate the new config within the same play.

Add `meta: flush_handlers` **right after** task `(3)`, then a smoke test:

```yaml
tasks:
  - name: Modifier nginx.conf (server_tokens)
    ansible.builtin.lineinfile:
      path: /etc/nginx/nginx.conf
      regexp: '^\s*server_tokens\s+'
      line: '    server_tokens off;'
      insertafter: '^http\s*\{'
    notify: Reload nginx

  - name: Forcer le reload immédiat
    ansible.builtin.meta: flush_handlers

  - name: Smoke test après reload
    ansible.builtin.uri:
      url: http://localhost
      status_code: 200
```

🔍 **Observation**: without `flush_handlers`, the `uri:` would test nginx **before** the reload, so with the old config. With `flush_handlers`, the order becomes: change → reload → test. This is the pattern found on deployments of critical configs (sshd, postgresql).

## 📚 Exercise 9 — Combine `validate:` + a handler (safety net)

The `lineinfile` module (and `template`) accepts a `validate:` argument that runs a command on the file **before** writing it in place. If the command fails, the original file is **not** replaced, and the handler is **not** notified (since `changed=false`).

```yaml
- name: Modifier nginx.conf avec validation syntaxique
  ansible.builtin.lineinfile:
    path: /etc/nginx/nginx.conf
    regexp: '^\s*server_tokens\s+'
    line: '    server_tokens off;'
    insertafter: '^http\s*\{'
    validate: nginx -t -c %s              # %s = path of the temp file
  notify: Reload nginx
```

🔍 **Observation**: if you deliberately set `line: '    server_tokens Garbage;'` (invalid), `nginx -t` fails, the original file stays intact, **and** the handler is not triggered. This is the **safety net** that prevents applying an invalid config in production.

> 💡 **Practical note**: `nginx.conf` truly validates because it is self-contained: its `include` (`mime.types`, `conf.d/*.conf`) are **absolute** paths, which nginx resolves from the temporary file `%s`. On `httpd.conf`, `validate:` failed precisely because the file references inclusions that cannot be found in this context. Try the command by hand, it is the contract that Ansible tests:
>
> ```bash
> sudo nginx -t -c /etc/nginx/nginx.conf   # returns 0 if OK, 1 if the config is broken
> ```

## 🔍 Observations to note

- A handler runs **only if** a task notifies it **and** is `changed`. No `changed` → no handler.
- Handlers are **deduplicated**: if 5 tasks notify the same handler, it runs only **once**.
- **`listen:`** = abstract topic. Lets you decouple tasks and handlers.
- **`meta: flush_handlers`** = flushes the queue immediately. Use it when the order `task → reload → test` must be strict within the same play.
- **`validate:`** is the safety net before writing. Combined with a handler, you **never** reload a service on a broken config.
- A handler **that fails when called** stops the play like a normal task. Keep handlers simple (a reload, a log), no complex logic inside.

## 🤔 Reflection questions

1. You have a play that modifies 5 nginx config files (vhosts, main, modules, etc.). You want **a single reload** at the end. How many handlers do you declare? How many notifications?

2. You want to restart a service **immediately** after a config change, but before the next task. Which keyword should you use, and why not a direct `state: restarted`?

3. How do you guarantee that a handler **never applies** an invalid config? Name the **two** complementary mechanisms.

## 🚀 Final challenge

The challenge ([`challenge/README.md`](challenge/README.md)) consolidates exercises 6-8 on `db1.lab`: two handlers, one task, and `meta: flush_handlers` to validate the config within the same play. Automated tests via `pytest+testinfra`:

```bash
pytest -v labs/ecrire-code/handlers/challenge/tests/
```

## 💡 Going further

- **`force_handlers: true`** at the play level: runs the pending handlers **even if a task fails** afterward. Handy to avoid leaving a service with a half-modified config.
- **Handlers in a role**: a role's handlers live in `roles/<role>/handlers/main.yml`, accessible via `notify:` from any task of the role, and even from outside.
- **Variables in `notify:`**: `notify: "{{ service_handler_name }}"` lets you parameterize the handler to call. Useful for generic roles (notify `Reload nginx` or `Reload apache` depending on a variable).
- **Saga pattern**: `pre_tasks` (DB snapshot) → `tasks` (config change) → `meta: flush_handlers` (reload) → `post_tasks` (smoke test) → handler `Restaurer snapshot` notified only on error. See lab 23 (block/rescue/always).

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/handlers/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/handlers/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/handlers/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.

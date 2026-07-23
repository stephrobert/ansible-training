# Lab 60 — Roles: `handlers/` and `meta/`

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

🔗 [**Ansible roles: handlers and meta**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/handlers-meta/)

In [lab 58](../creer-premier-role/), you created your first
role (the `tasks/main.yml` skeleton). In [lab 59](../variables-defaults-vars/),
you saw `defaults/` and `vars/`. This lab covers **the last two
fundamental sub-directories** of a role:

| Directory | Role | Visibility |
| --- | --- | --- |
| `handlers/main.yml` | **Reactive** tasks triggered by `notify:` | The role's tasks + external tasks (if the role is included) |
| `meta/main.yml` | The role's **identity card** (Galaxy info, platforms, dependencies) | Read by `ansible-galaxy`, `ansible-lint`, and dependency resolution |

> 💡 **Key difference** with a play's handlers: the role's handlers live
> in the **role's scope**. A `Restart nginx` handler in `roles/webserver/handlers/`
> is callable by `notify: Restart nginx` from anywhere, including
> from another role or from the parent play.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Write a `handlers/main.yml` file with **several handlers** (Restart, Reload, custom Notification).
2. Distinguish **`state: restarted`** vs **`state: reloaded`** in a handler: when to use one or the other.
3. Notify a handler with **`notify:`** on a role's task.
4. Write a **non-service handler** (e.g. log, webhook, file): a handler is not only a `systemd_service`.
5. Complete `meta/main.yml` with **`galaxy_info`**, **`platforms`**, **`galaxy_tags`**, **`min_ansible_version`**, **`license`**.
6. Understand **`dependencies: []`** and **`allow_duplicates: false`**.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ansible.builtin.ping
ansible db1.lab -b -m ansible.builtin.shell \
    -a "rm -f /var/log/webserver-deploy.log /var/log/deploy-notification.log"
```

## ⚙️ Lab tree

```text
labs/roles/handlers-meta/
├── README.md                                ← this file
├── roles/
│   └── webserver/                           ← reference role shipped
│       ├── tasks/main.yml                   ← notifies 3 different handlers
│       ├── handlers/main.yml                ← TO STUDY (3 handlers)
│       ├── defaults/main.yml                ← (recap lab 59)
│       ├── meta/main.yml                    ← TO STUDY (galaxy_info)
│       └── templates/nginx.conf.j2
└── challenge/
    ├── README.md                            ← challenge instructions
    └── tests/
        └── test_handlers.py                 ← pytest+testinfra
```

> ⚠️ **Convention**: the `webserver` role is shipped pre-written for this lab.
> The goal is **not** to rewrite the role, but to **understand** and
> **use** its handlers + to **read** its `meta/`.

## 📚 Exercise 1 — Read `handlers/main.yml`

Open `roles/webserver/handlers/main.yml`:

```yaml
- name: Restart nginx
  ansible.builtin.systemd_service:
    name: "{{ webserver_package }}"
    state: restarted

- name: Reload nginx
  ansible.builtin.systemd_service:
    name: "{{ webserver_package }}"
    state: reloaded

- name: Notify deployment
  ansible.builtin.copy:
    dest: /var/log/deploy-notification.log
    content: |
      Deployment completed
      Host: {{ inventory_hostname }}
      Webserver port: {{ webserver_listen_port }}
    mode: "0644"
```

🔍 **Observation**: 3 handlers, 3 use cases:

| Handler | When to trigger it? | Effect |
| --- | --- | --- |
| `Restart nginx` | After deleting a config file (`conf.d/default.conf`), requires a full restart | Downtime ~1s |
| `Reload nginx` | After modifying `nginx.conf`, nginx can reload live (SIGHUP) | No downtime |
| `Notify deployment` | At the end of a successful deployment, purely informational | No service impact |

**General rule**:

- **Reload** > Restart when the service supports it (HUP signal). No downtime.
- **Restart** on a major change (upgraded binary, config incompatible with live reload).
- A handler can be **any task**, not only `systemd_service`. Here we log to a file.

## 📚 Exercise 2 — Read `tasks/main.yml` (who notifies what)

Open `roles/webserver/tasks/main.yml`. Spot the `notify:`:

| Task | `notify:` | Why |
| --- | --- | --- |
| Delete the conflicting default config | `Restart nginx` | File deletion → reload is not enough |
| Deploy nginx.conf from the template | `Reload nginx` | Config change → SIGHUP is enough |
| Deploy the welcome page | (none) | HTML page, nginx serves it without a reload |
| Trace the deployment | `Notify deployment` | Final log, after everything else |

🔍 **Observation**: a handler is notified only if the task is `changed`.
That is the whole mechanic, and it is earned: the "Tracer le
déploiement" task writes **stable** content (the host and the applied
port), so it only reports `changed` when the deployed state really changes. The
`Notify deployment` handler only runs at that moment.

> ⚠️ **The pitfall this role avoids**: putting `{{ ansible_date_time.iso8601 }}`
> in the `content:`. The content then differs on every run, `copy:` reports
> **`changed` every time**, and the handler fires on every execution even when
> nothing moved. This is exactly the production complaint in this lab's scenario. A
> timestamp in a file under `copy:` does not trace a deployment: it fabricates a
> fake change.

## 📚 Exercise 3 — Read `meta/main.yml`

Open `roles/webserver/meta/main.yml`:

```yaml
galaxy_info:
  author: Stéphane Robert
  namespace: stephrobert
  role_name: webserver
  description: |
    Installer et configurer nginx ...
  license: MIT
  min_ansible_version: "2.16"

  platforms:
    - name: EL
      versions: ["9", "10"]
    - name: AlmaLinux
      versions: ["9", "10"]

  galaxy_tags: [nginx, webserver, http, rhce]

dependencies: []
allow_duplicates: false
```

🔍 **Observation**: each field has its role:

| Field | Role | Consequence if absent |
| --- | --- | --- |
| `author`, `namespace`, `role_name` | Galaxy identity | Impossible to publish on Galaxy |
| `description` | Displayed on the Galaxy page | Unattractive page |
| `license` | Legal license (MIT, GPLv3, …) | Galaxy refuses publication |
| `min_ansible_version` | Minimum supported Ansible version | Risk of a silent bug on old Ansible |
| `platforms` | OS supported by the role | Galaxy filters by OS |
| `galaxy_tags` | Tags for search | Role invisible in searches |
| `dependencies: []` | List of dependent roles | (no dependencies here, lab 72 covers it) |
| `allow_duplicates: false` | Refuses multiple inclusion of the role | Best practice except in special cases |

## 📚 Exercise 4 — Run the role and observe the handlers

Create a `playbook.yml` at the root of the lab that uses the role:

```yaml
---
- name: Démo handlers du rôle webserver
  hosts: db1.lab
  become: true
  roles:
    - role: webserver
```

Run it:

```bash
ansible-playbook labs/roles/handlers-meta/playbook.yml
```

🔍 **Observation**: console output (excerpt):

```text
TASK [webserver : Supprimer la conf par défaut ...] *** changed (1st run)
TASK [webserver : Déployer nginx.conf ...]            *** changed (1st run)
TASK [webserver : Tracer le déploiement]              *** changed (1st run)

RUNNING HANDLER [webserver : Restart nginx]           *** changed
RUNNING HANDLER [webserver : Reload nginx]            *** changed
RUNNING HANDLER [webserver : Notify deployment]       *** changed
```

**3 handlers triggered** on the 1st run.

```bash
# Check the log files
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo cat /var/log/webserver-deploy.log'
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo cat /var/log/deploy-notification.log'
```

On the **2nd run**, without changing anything: `PLAY RECAP` reports `changed=0` and
**no `RUNNING HANDLER` banner appears**. The three tasks find the state already
compliant, none reports `changed`, so no handler is notified. This is the very
definition of an idempotent role, and it is what the challenge's
`test_solution_idempotente` test checks.

Now re-run, changing the port:

```bash
ansible-playbook labs/roles/handlers-meta/playbook.yml -e webserver_listen_port=8081
```

There, `Déployer nginx.conf` and `Tracer le déploiement` report `changed` (both
the template and the trace carry the port), so `Reload nginx` and
`Notify deployment` fire again. **A handler reacts to a change of state,
not to the passing of time.**

## 🔍 Observations to note

- **A role's handlers** live in `handlers/main.yml`. They are scoped to the
  role but notifiable from the outside (with the `<role_name> :` prefix).
- **`reloaded` > `restarted`** when the service supports it (nginx, apache,
  postgresql, sshd…). No downtime.
- **A handler can be any task**: copy, debug, uri,
  shell. Not reserved for `systemd_service`.
- **`meta/main.yml`** is read by `ansible-galaxy`, `ansible-lint --profile
  production`, and the dependency mechanism. **Always fill it in**
  for a role you share.
- **`allow_duplicates: false`** (default): prevents including the same role
  several times in a play. Set it to `true` only if you want to
  apply the same role with different params (e.g. deploy 3
  nginx vhosts).

## 🤔 Reflection questions

1. You have 3 tasks that modify `nginx.conf`. How many times does the
   `Reload nginx` handler run? Why?

2. Replace the `content:` of "Tracer le déploiement" with
   `"Deployed at {{ ansible_date_time.iso8601 }}\n"` and replay twice.
   How many `changed` on the second run? Which handlers fire again, and why
   is it an idempotence anti-pattern? Then restore the stable content.
   (Caution: `ansible.cfg` caches facts for 2 hours, so
   `ansible_date_time` is **frozen**. Without `ANSIBLE_CACHE_PLUGIN=memory`, the
   default gets cached and you will wrongly see `changed=0`.)

3. You want your role to depend on `geerlingguy.firewall` (to open the
   ports). In which field of `meta/main.yml` do you declare it? (Hint:
   lab 72 covers it.)

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`listen:`** on a handler: lets several handlers listen to a
  same abstract topic (see lab 06).
- **`meta: flush_handlers`**: forces immediate execution of the pending
  handlers (see lab 06).
- **`force_handlers: true`** at play level: runs the pending handlers
  even if a task fails afterwards. Valuable to avoid leaving a
  service in a half-modified config.
- **`dependencies:`** in `meta/main.yml`: list other roles to run
  **before** yours. Covered in lab 72.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `playbook.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint the full role
ansible-lint labs/roles/handlers-meta/roles/webserver/

# Lint your challenge solution
ansible-lint labs/roles/handlers-meta/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/roles/handlers-meta/
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices.

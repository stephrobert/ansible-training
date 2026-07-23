# 🎯 Challenge — Granular sudo rules

## ✅ Objective

On **db1.lab**, create **3 sudo rules** in `/etc/sudoers.d/` via the
`community.general.sudoers` module.

## 🧩 Rules to provision

| File | User/Group | Commands | Password? | RunAs |
| --- | --- | --- | --- | --- |
| `lab-rhce-alice` | user `alice` | `ALL` | **yes** (with password) | (default) |
| `lab-rhce-ops-team` | group `ops-team` | `ALL` | no (`NOPASSWD`) | (default) |
| `lab-rhce-alice-as-deploy` | user `alice` | `/opt/myapp/bin/deploy.sh` | no | `deploy` |

## 🧩 Prerequisites (`users` step)

Before the sudo rules, create:

- Users: `alice`, `bob`, `deploy`.
- Group: `ops-team`.
- `bob` member of the `ops-team` group (`groups: ops-team, append: true`).

## 🧩 Stuck?

```bash
dsoxlab hint modules-utilisateurs-sudoers
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🧩 Skeleton

```yaml
---
- name: Challenge - règles sudo granulaires
  hosts: db1.lab
  become: true

  tasks:
    - name: Pré-requis users
      ansible.builtin.user:
        name: "{{ item }}"
        state: present
        shell: /bin/bash
      loop: ???

    - name: Pré-requis groupe ops-team
      ansible.builtin.group:
        name: ???
        state: present

    - name: bob membre de ops-team
      ansible.builtin.user:
        name: ???
        groups: ???
        append: ???

    - name: Sudo complet pour alice (avec password)
      community.general.sudoers:
        name: ???
        user: ???
        commands: ???
        nopassword: ???
        state: present

    - name: Sudo complet pour ops-team (NOPASSWD)
      community.general.sudoers:
        name: ???
        group: ???
        commands: ???
        nopassword: ???
        state: present

    - name: alice peut lancer deploy.sh en tant que deploy
      community.general.sudoers:
        name: ???
        user: ???
        runas: ???
        commands: ???
        nopassword: ???
        state: present
```

> 💡 **Traps**:
>
> - **`nopassword:`** is `true` by default on `community.general.sudoers`.
>   To require a password: **`nopassword: false`** explicitly.
>   Classic forgetful mistake.
> - **`commands:`** accepts a **list**. Format: absolute path of the
>   command (`/usr/bin/systemctl`), not just the name.
> - **`runas:`** = destination user of `sudo`. By default
>   `root`. For `sudo -u app`: `runas: app`.
> - **Generated file**: `/etc/sudoers.d/<name>` (not `/etc/sudoers`).
>   `validate: 'visudo -cf %s'` is applied automatically by the module.

## 🚀 Run

```bash
ansible-playbook labs/modules-utilisateurs/sudoers/challenge/solution.yml
ansible db1.lab -b -m ansible.builtin.shell -a "ls -la /etc/sudoers.d/lab-rhce-*"
ansible db1.lab -b -m ansible.builtin.shell -a "visudo -cf /etc/sudoers"
```

## 🧪 Automated validation

```bash
pytest -v labs/modules-utilisateurs/sudoers/challenge/tests/
```

The test checks in particular the **strict 0440 permissions** on the files
(otherwise `sudo` ignores them for safety).

## 🧹 Reset

```bash
dsoxlab clean modules-utilisateurs-sudoers
```

## 💡 Going further

- **`validation: required`**: Ansible validates the syntax via `visudo` before
  writing the file. If the generated file is invalid, the write fails (safety
  net, the original file stays intact).
- **`Defaults`**: to set `Defaults env_keep+="HTTP_PROXY"` or
  `Defaults requiretty`, use `setenv:` or edit `/etc/sudoers.d/` directly via
  `template:`.
- **Lint**:

   ```bash
   ansible-lint labs/modules-utilisateurs/sudoers/challenge/solution.yml
   ```

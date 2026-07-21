# 🎯 Challenge — SELinux to serve a custom web app

## ✅ Objective

On **db1.lab**, prepare **SELinux** so that the web server (nginx) can:

1. Make **outbound network connections** (boolean
   `httpd_can_network_connect`).
2. **Serve** files from a **custom** directory (`/var/www/myapp/`)
   by setting the SELinux context `httpd_sys_content_t`.

This is a classic RHCE case: deploy an app in a directory that is not
the default web root (`/usr/share/nginx/html/` for nginx on RHEL).

> 💡 **Why booleans and a type prefixed `httpd_` when we deploy
> nginx?** Because on RHEL, nginx runs in the **SELinux domain
> `httpd_t`**, the generic domain of web servers in the targeted policy.
> Check it: `ps -eZ | grep nginx` shows `system_u:system_r:httpd_t:s0`.
> `httpd_can_network_connect` and `httpd_sys_content_t` therefore apply to
> nginx exactly as to Apache. The `httpd` package is never required for
> this lab.

## 🧩 6 steps

1. **Install prerequisites**: `python3-libselinux` and
   `policycoreutils-python-utils` (the Ansible SELinux modules depend on these
   binaries on the managed node).
2. **SELinux enforcing**: `state: enforcing`, `policy: targeted`.
3. **Enable the boolean** `httpd_can_network_connect` (persistent).
4. **Create the directory** `/var/www/myapp/` (mode 0755).
5. **Define the context** `httpd_sys_content_t` on `/var/www/myapp(/.*)?`
   via `community.general.sefcontext` (path regex).
6. **Apply the context** with `restorecon -R /var/www/myapp` (without this
   step, the context is in the **policy** but not on the existing **files**).

## 🧩 Modules to use

| Module | Role |
| --- | --- |
| `ansible.posix.selinux` | Global mode (enforcing/permissive/disabled) |
| `ansible.posix.seboolean` | Enable/disable a SELinux boolean |
| `community.general.sefcontext` | Define a context on a path (regex) |
| `ansible.builtin.command: restorecon ...` | Apply the context |

## 🧩 Skeleton

```yaml
---
- name: Challenge - SELinux pour app web custom
  hosts: db1.lab
  become: true

  tasks:
    - name: Installer prérequis SELinux
      ansible.builtin.dnf:
        name: ???
        state: present

    - name: SELinux enforcing
      ansible.posix.selinux:
        policy: ???
        state: ???

    - name: Activer le booléen httpd_can_network_connect
      ansible.posix.seboolean:
        name: ???
        state: ???
        persistent: ???

    - name: Créer /var/www/myapp
      ansible.builtin.file:
        path: ???
        state: directory
        mode: "0755"

    - name: Définir le contexte httpd_sys_content_t
      community.general.sefcontext:
        target: ???        # regex: '/var/www/myapp(/.*)?'
        setype: ???
        state: present

    - name: Appliquer le contexte avec restorecon
      ansible.builtin.command: restorecon -R /var/www/myapp
      changed_when: false
```

> 💡 **Traps**:
>
> - **`seboolean`** is in **`ansible.posix`**. **`sefcontext`** is in
>   **`community.general`**. Tell the FQCNs apart carefully.
> - **`sefcontext`** modifies the **policy** but does not apply
>   immediately. `restorecon` is needed to apply it to the existing
>   files.
> - **`persistent: true`** on `seboolean`: survives the reboot. Without it,
>   the boolean falls back to the default at the next boot.
> - **`python3-libselinux`** must be installed on the target. Without it, the
>   `seboolean`/`sefcontext` modules crash with an unclear error.

## 🚀 Run

```bash
ansible-playbook labs/modules-rhel/selinux/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "getenforce"
ansible db1.lab -m ansible.builtin.command -a "getsebool httpd_can_network_connect"
ansible db1.lab -m ansible.builtin.command -a "ls -dZ /var/www/myapp"
```

## 🧪 Automated validation

> ⏱️ **One test reboots db1** (about 90 s). It is marked `slow`, and it is
> there on purpose: persistence after a restart is the trap that fails RHCSA
> and RHCE candidates, and reading the config file proves nothing about it.
> While you iterate, you can leave it out:
>
> ```bash
> pytest -m 'not slow' labs/modules-rhel/selinux/challenge/tests/
> ```
>
> Run the full suite at least once before considering the challenge done.

```bash
pytest -v labs/modules-rhel/selinux/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean modules-rhel-selinux
```

## 💡 Going further

- **`getsebool -a`**: lists all SELinux booleans and their state.
- **`semanage fcontext -l | grep myapp`**: see the contexts defined in
  the policy (what `sefcontext` modifies).
- **AVC denials**: `ausearch -m AVC -ts recent` to see the recent SELinux
  denials, valuable to understand why a service does not start.
- **Lint**:

   ```bash
   ansible-lint labs/modules-rhel/selinux/challenge/solution.yml
   ```

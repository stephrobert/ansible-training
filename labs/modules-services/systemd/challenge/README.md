# 🎯 Challenge — `systemd_service` + custom unit file

## ✅ Objective

On **web1.lab**, manage the standard service **`chronyd`** AND create a
**custom unit file** `lab-marker.service` (oneshot) that touches a flag
file at startup.

> 💡 **Why `chronyd` and not `nginx`?** `nginx` already occupies ports
> 80/443 of `web1.lab` for other labs. `chronyd` (NTP, port 123 UDP) creates
> no conflict, and the `systemd_service` module is used exactly the
> same way regardless of the service: it is the subject, not the daemon.

## 🧩 4 steps

1. **Install** `chrony` via `dnf`.
2. **Start + enable** `chronyd` at boot via `systemd_service:`.
3. **Create** the file `/etc/systemd/system/lab-marker.service` via
   `copy: content:` with an inline unit file.
4. **Reload systemd** (`daemon_reload: true`) AND enable/start
   `lab-marker`.

## 🧩 Expected content of `lab-marker.service`

```ini
[Unit]
Description=Lab Marker Service
After=network.target

[Service]
Type=oneshot
ExecStart=/bin/touch /var/run/lab-marker.flag
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

> 💡 **`Type=oneshot` + `RemainAfterExit=yes`**: the service runs its
> `ExecStart` once then stays marked `active` (otherwise it would be `inactive`
> as soon as the `touch` finishes). Classic pattern for "init" non-daemon
> services.

## 🧩 Skeleton

```yaml
---
- name: Challenge - systemd_service avec unit file custom
  hosts: web1.lab
  become: true

  tasks:
    - name: Installer chrony
      ansible.builtin.dnf:
        name: ???
        state: present

    - name: Démarrer et activer chronyd
      ansible.builtin.systemd_service:
        name: ???
        state: ???
        enabled: ???

    - name: Créer le unit file lab-marker.service
      ansible.builtin.copy:
        dest: ???
        mode: "0644"
        content: |
          [Unit]
          Description=Lab Marker Service
          After=network.target

          [Service]
          Type=oneshot
          ExecStart=/bin/touch /var/run/lab-marker.flag
          RemainAfterExit=yes

          [Install]
          WantedBy=multi-user.target

    - name: Recharger systemd, activer et démarrer lab-marker
      ansible.builtin.systemd_service:
        name: ???
        daemon_reload: ???
        enabled: ???
        state: ???
```

> 💡 **Traps**:
>
> - **`daemon_reload: true`** is mandatory **after modifying** a
>   unit file. Otherwise systemd ignores the changes (cache).
> - **`state:`** = `started`, `stopped`, `restarted`, `reloaded`. Use
>   `restarted` in **handlers**, not in tasks (otherwise non-idempotent
>   by default).
> - **`enabled: true`** = at boot. Not equivalent to `started: true`
>   (running now). For both together: `state: started` +
>   `enabled: true`.
> - **No `.service` in `name:`**: just `nginx`, not
>   `nginx.service`. Except to disambiguate (timer, socket).

## 🚀 Run

```bash
ansible-playbook labs/modules-services/systemd/challenge/solution.yml
ansible web1.lab -m ansible.builtin.command -a "systemctl is-active chronyd lab-marker"
ansible web1.lab -m ansible.builtin.command -a "ls -la /var/run/lab-marker.flag"
```

## 🧪 Automated validation

```bash
pytest -v labs/modules-services/systemd/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean modules-services-systemd
```

## 💡 Going further

- **`state: restarted`** vs **`state: reloaded`**: `restarted` is
  destructive (downtime), `reloaded` sends `SIGHUP` (no downtime, but
  only if the service supports it).
- **`scope: user`**: manage a **user** systemd service
  (`~/.config/systemd/user/`) instead of a system service.
- **`masked: true`**: prevents the manual or automatic start of a
  service (redirects to `/dev/null`).
- **Lint**:

   ```bash
   ansible-lint labs/modules-services/systemd/challenge/solution.yml
   ```

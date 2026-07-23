# Challenge `yum_repository:`

## Statement

On **db1.lab** (AlmaLinux 9), write `solution.yml` that brings the machine
into this state:

1. The **EPEL** repository matching the distribution version is
   declared in `/etc/yum.repos.d/epel.repo`, **enabled** and with
   **mandatory GPG verification** (key imported, `gpgcheck` active).
   The official URLs:
   - baseurl: `https://dl.fedoraproject.org/pub/epel/<version>/Everything/$basearch/`
   - GPG key: `https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-<version>`
2. The **`htop`** package (provided by EPEL, absent from the base repos) is
   **installed**.
3. A **`local-test`** repo is declared in
   `/etc/yum.repos.d/local-test.repo`, baseurl `file:///srv/repo/`,
   **present but disabled**: the file exists, the repo is never used.
4. A 2nd run of the playbook changes nothing (idempotent).

## Success criteria

- `/etc/yum.repos.d/epel.repo` exists and contains `enabled = 1`.
- `rpm -q htop` returns the package name + version.
- `/etc/yum.repos.d/local-test.repo` exists and contains `enabled = 0`.
- `dnf repolist enabled | grep local-test` returns **nothing**.
- 2nd run of the playbook: `changed: 0`.

## 🧩 Stuck?

```bash
dsoxlab hint modules-paquets-yum-repository
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

# Open EPEL under signature, stage the local repo shut

## The situation

The monitoring team needs `htop` on **db1.lab**, and the base repositories
do not ship it: it lives in **EPEL**. The security policy is explicit:
nothing gets installed from an unsigned source, so the repository comes in
with its GPG key imported and signature checking on. Meanwhile the build
team is preparing an internal RPM repository served from local disk; it must
be **declared now but stay shut** until its content is vetted, because a
declared-and-enabled repo silently joins every future `dnf update`. All of
it driven from **control-node.lab**, and rerunnable without a single change
on the second pass.

Your mission:

1. Import the **EPEL GPG key** on **db1.lab**, then declare the EPEL
   repository matching the distribution release, **enabled and
   signature-checked**.
2. Install **`htop`** from it.
3. Declare the **`local-test`** repository (`file:///srv/repo/`),
   **disabled**: the `.repo` file exists on disk, the repo never serves.
4. Prove it: the package is installed, EPEL shows up enabled, `local-test`
   stays out of the enabled list, and a second run reports `changed: 0`.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-yum-repository/ (in French)

## Challenge `yum_repository:`

### Statement

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

### Success criteria

- `/etc/yum.repos.d/epel.repo` exists and contains `enabled = 1`.
- `rpm -q htop` returns the package name + version.
- `/etc/yum.repos.d/local-test.repo` exists and contains `enabled = 0`.
- `dnf repolist enabled | grep local-test` returns **nothing**.
- 2nd run of the playbook: `changed: 0`.

### 🧩 Stuck?

```bash
dsoxlab hint modules-paquets-yum-repository
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

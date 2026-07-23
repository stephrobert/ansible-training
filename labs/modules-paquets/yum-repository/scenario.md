# Context — Open EPEL under signature, stage the local repo shut

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
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-yum-repository/

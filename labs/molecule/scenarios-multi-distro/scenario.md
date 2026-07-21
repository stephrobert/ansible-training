# Context — The role is going public, and it only knows RHEL

Your `webserver` role is about to be published, and the first issue is already
predictable. It calls `dnf` directly, writes to `/usr/share/nginx/html` and
assumes the service runs as `nginx`. On Debian the package manager is wrong, the
document root is elsewhere and the user is `www-data`. The role does not work
anywhere else, and worse, the test suite has no way to notice: it only ever
tested the one distribution the author happened to run.

Your mission, from the project directory:

1. Extend the test matrix to **three distributions** across at least two OS
   families, so the suite fails the day portability breaks.
2. Pull the divergent facts (package name, document root, service user) out of
   the tasks and into **per-OS variable files** loaded from the target's own
   detected family.
3. Replace the distribution-specific package calls with the **agnostic** module,
   so the role stops choosing the package manager on the caller's behalf.
4. Verify the **same** role converges on all three platforms, unmodified.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/molecule-scenarios-multi-distro/

# Context — Prepare the release tree before the first deploy

The dev team ships **myapp** to **web1.lab** on Thursday and expects the
filesystem to be ready: a versioned release directory, a `current` symlink the
service reads, and a log directory the application can write to without running
as root. The previous hand-made attempt left a stale `/etc/myapp-old.conf`
behind that the app still picks up. You prepare the ground from
**control-node.lab**, in a playbook that will be replayed on every release.

Your mission:

1. Build the release tree on **web1.lab**: **`/opt/myapp/releases/v1.0.0`**
   (mode `0755`, root) and **`/opt/myapp/shared/logs`** (mode `0750`, owned by
   `nobody`) so the app writes its logs without privileges.
2. Point **`/opt/myapp/current`** at the `v1.0.0` release, **overwriting** any
   symlink already aiming elsewhere.
3. Remove the leftover **`/etc/myapp-old.conf`** and drop the init marker
   **`/var/log/myapp-init.timestamp`** (mode `0644`).

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-file/

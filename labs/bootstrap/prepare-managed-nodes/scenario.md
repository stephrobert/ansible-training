# Context — Three fresh nodes, nothing but a key

Provisioning just handed you **web1.lab**, **web2.lab** and **db1.lab**.
Cloud-init did the strict minimum: an `ansible` user, an SSH key, passwordless
sudo. Nothing else. Their clocks already disagree, they cannot resolve each
other by name, and SELinux is anybody's guess. Every playbook of this training
will run against them, so they must first be **identical and predictable**.
From **control-node.lab**, you write the bootstrap that makes Ansible prepare
its own fleet.

Your mission:

1. Converge the **base prerequisites** on the three managed nodes: the Python
   helper packages the modules need, and `chrony` running so the facts share a
   single clock.
2. Make every node **resolve** `web1.lab`, `web2.lab`, `db1.lab` and
   `control-node.lab`.
3. Pin the baseline: **SELinux enforcing** with the `targeted` policy, timezone
   **Europe/Paris**.
4. Prove this is a **bootstrap and not a script**: a second run must report
   `changed=0` on all three nodes.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/premiers-pas/preparer-noeuds-geres/

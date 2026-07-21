# Context: there is no inventory yet, and nothing runs without one

The other inventory labs handed you a ready-made `hosts.yml` and let you play
with patterns and variables. In the real world, and on exam day, nobody hands
you that file: **you write it**. The very first task of the RHCE mock exam is
"create the static host inventory", and every playbook you will ever run reads
from it. An inventory that is missing, or that puts the wrong host in the wrong
group, makes every later task target the wrong machines.

You are on **control-node.lab**, facing three managed nodes: two web servers
(**web1.lab**, **web2.lab**) and one database server (**db1.lab**). No
inventory exists.

Your mission:

1. Write a **static inventory from scratch**, by hand, no generator.
2. Declare two host groups: **`webservers`** (web1 + web2) and **`dbservers`**
   (db1).
3. Declare a **parent group** `datacenter` that aggregates both, using
   **`children`**.
4. Add **group variables**: one scoped to `webservers`, one carried by the
   parent `datacenter` so every host inherits it.
5. Never hardcode an IP address: connection goes through the dsoxlab
   `ssh_config`, and the SSH user is `student`.

You prove nothing by showing the file. You prove it by asking Ansible what it
resolves (`ansible-inventory --list`) and by joining exactly the right hosts
(`ansible <group> -m ping`).

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/statiques-yaml/

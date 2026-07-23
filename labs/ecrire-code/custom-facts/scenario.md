# Context — The host that has to say who owns it

Half the fleet has no owner. When a machine misbehaves at 2 a.m., the on-call
engineer has to guess which team to wake, and the only answer lives in a wiki
page a year out of date. The inventory cannot help: it describes what Ansible
manages, not what the machine carries. So the machine is going to say it
itself, and Ansible will read it back at every run, next to the facts it
already collects.

You start with **db1.lab**, from **control-node.lab**.

Your mission:

1. Drop a **static INI custom fact** on db1 declaring the project it belongs
   to, its version, and the team that owns it.
2. Drop a second fact that is an **executable script returning JSON**: the
   things no static file can know, such as the running kernel and the uptime.
3. Get the modes right: a static fact is read, a dynamic one must be
   **executable**. The wrong mode is the classic failure here, and its error
   message will not help you.
4. Re-collect the facts, then read both back through **`ansible_local`** and
   write the proof file on db1.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/custom-facts/

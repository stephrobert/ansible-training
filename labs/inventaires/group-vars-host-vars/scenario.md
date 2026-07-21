# Context — Settle the argument about which port the app really uses

The team has been going in circles for two days. The application listens on the
standard port everywhere, except on the web tier, which uses another, except on
**web1.lab**, which was moved again for a conflict nobody documented. Three
different answers depending on who you ask, and the variable is spread across
three inventory levels that override each other. Reading the YAML is not enough:
what settles it is what Ansible **resolves at runtime**, on each host, from
**control-node.lab**.

Your mission:

1. Spread the application port across the inventory's **three levels**: the
   default for everyone, the web tier's override, and **web1.lab**'s specific
   value.
2. Write a play targeting **all hosts** that drops on each one a marker holding
   **the port resolved for that host**, named after the host itself.
3. Prove the precedence on the three managed nodes: **web1.lab** takes its
   host-level value, **web2.lab** takes the group's, and **db1.lab** falls back
   to the default.
4. Run it against the **lab inventory**, without which none of the group
   variables load and the demonstration proves nothing.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/group-vars-host-vars/

# Context — one tool to find the module, use it, and check the inventory

Your team is standardising on **Automation content navigator**. The old reflex was
`ansible-doc` here, `ansible-inventory` there, `ansible-playbook` to finish: three
commands, three behaviours, nothing that maps to what production actually runs
(Execution Environments). The RHCE exam now expects you to reach for
`ansible-navigator` for the whole loop.

A colleague needs a kernel parameter set on **db1.lab** but does not remember which
module does it or which collection ships it. Rather than guessing, you will *find*
the module with the navigator, then *use* it, then *validate* the inventory the play
will target, all with the same tool.

Your mission, from **control-node.lab**:

1. Use `ansible-navigator doc` to find the module that manages `sysctl` entries,
   confirm the collection it comes from, and keep a **proof** of that exploration
   on `db1.lab` (the module's fully qualified name must appear in it).
2. Use that discovered module to set `vm.swappiness = 42` on `db1.lab`, live and
   persistent, in an idempotent way.
3. Write a small inventory and validate it with `ansible-navigator inventory
   --list`, then keep the resolved output as proof on `db1.lab`.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/ansible-navigator/

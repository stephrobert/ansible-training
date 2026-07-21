# Context — "Why is my tag not applying to the included tasks?"

The playbook reached four hundred lines, so it was split into task files. Then
things turned strange: tags stopped selecting what people expected, one file
had to run once per environment and flatly refused to loop, and
`--list-tasks` showed only half the plan. Nothing is broken. Ansible has two
ways of pulling a file in — one resolved before the run starts, one resolved as
the run unfolds — and they do not behave alike.

You separate the two on `db1.lab`, from **control-node.lab**.

Your mission:

1. Pull in a fixed set of tasks **statically**, parsed before the play even
   begins, and watch it appear in the plan.
2. Pull a second file in **dynamically**, once per item of a loop — and find
   out why the static form cannot do this at all.
3. Get the paths right: a task file resolves **relative to the playbook**, not
   to the directory you are standing in.
4. Prove both mechanisms ran: the static marker on db1, plus one marker per
   iteration.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/import-include/

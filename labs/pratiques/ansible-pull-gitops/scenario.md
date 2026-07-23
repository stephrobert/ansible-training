# Context — Four hundred nodes your control node will never reach

The new fleet lives in shops behind consumer routers: no public address, no
inbound SSH, sometimes offline for a day. Your control node cannot reach any of
them, and the push model has run out of road. There is no more central machine
opening connections outward. If a node wants its configuration, it will have to
go and get it, from the one thing it can always reach: a Git repository.

Your mission, from the project directory:

1. Publish the configuration as a **Git repository** and have the target pull it
   and apply it **to itself**, no control node in the loop.
2. Prove it ran by having the pulled play leave evidence on the node it was
   executed from, not on the machine that wrote the playbook.
3. Make it **autonomous**: schedule the pull so the node converges on its own, and
   arrange for a freshly provisioned machine to bootstrap itself on first boot.
4. Draw the line for your team: what push still does better, what pull buys you at
   the edge or at four hundred nodes, and what you give up in exchange.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/pratiques/ansible-pull-gitops/

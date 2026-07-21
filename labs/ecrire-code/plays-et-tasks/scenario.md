# Context — "The restart happened after the all-clear"

Last deployment on **db1.lab** left the team puzzled: the maintenance banner
went up before the service was even installed, and the restart landed after the
post-deployment notification had already been sent. Nobody wrote a bug. The
playbook was one long flat `tasks:` list, so everything ran in writing order,
and nothing ran in the right one. A play has sections, and they exist for
exactly this.

You rewrite it properly from **control-node.lab**.

Your mission:

1. Structure a play on `db1.lab` around **`pre_tasks`**, **`tasks`**,
   **`post_tasks`** and **`handlers`**.
2. Deploy `nginx`, started and enabled, serving a page that identifies the host
   by its inventory name.
3. Make the config change **notify** a restart handler instead of restarting on
   every single run.
4. Prove the real execution order with **timestamped marker files**: the
   pre-deploy marker must be older than the post-deploy one.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/plays-et-tasks/

# Context — The reset task that must never fire by accident

The `db1.lab` playbook does three things: it runs a pre-flight check, it
applies the routine config, and it holds a **reset** routine that wipes the
host's state clean. That last one is legitimate, someone needs it when a node
is rebuilt. But it lives in the same file, and it has already fired once,
triggered by a tired engineer who only wanted to push a config change. You are
not going to split the file. You are going to make the reset unreachable unless
someone asks for it by name, from **control-node.lab**.

Your mission:

1. Tag the routine config task so `--tags configuration` touches it and nothing
   else.
2. Make the pre-flight marker run **whatever** the operator asked for, using the
   `always` tag.
3. Lock the destructive reset behind **`never`**, alongside its own `reset` tag:
   skipped by default, skipped even on a bare run, reachable only on demand.
4. Verify by running with `--tags configuration`: the `always` and
   `configuration` markers are there, the reset marker is not.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/tags/

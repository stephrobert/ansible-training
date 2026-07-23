# Context — Clean up the oversized logs without deleting the useful ones

An application on **db1.lab** has been dumping logs into `/tmp` for weeks, and a
few of them have grown fat enough to threaten the partition. The rule the team
agreed on is simple: past a certain size, the log goes; below that, it stays,
because the small ones are still what you read when debugging. Nobody wants a
`rm` recited from memory at 2 a.m. on a production box. You drive the cleanup
from **control-node.lab**, and Ansible decides what goes.

Your mission:

1. Set up the working directory and its log files on **db1.lab**: the ground
   this cleanup will run against.
2. **Search** that directory for the `.log` files **over 5 MB**, letting the
   search module do the filtering rather than a shell one-liner.
3. **Delete only the files it found**, by iterating over the search result: what
   is not on the list is not touched.
4. Prove the outcome: the small logs survive, the big ones are gone.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-find/

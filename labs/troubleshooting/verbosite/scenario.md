# Context — Twenty minutes of guessing, and a password in the CI logs

A task fails on **db1.lab** with a message that says nothing useful, and the team
reflex is to re-run it with every `-v` the keyboard can hold. That dumps thousands
of lines, and buries the one that mattered. Then someone noticed the real damage:
a task handling a token had printed its arguments in full into a log everyone can
read. Verbosity is a scalpel, and the team is using it as a hammer, on a playbook
that was never told to keep its mouth shut.

Your mission, from **control-node.lab**:

1. Match the **verbosity level to the symptom**: which level shows the arguments a
   module actually received after templating, and which one is about the SSH
   connection and has nothing to say about your bug.
2. Enable **task profiling** on a play of three measurable tasks against
   **db1.lab**, without touching the tasks themselves, and read the timings.
3. Make the output legible: switch the terminal callback for one a human can scan
   during an incident, and drop the profiling proof into a file on the target.
4. Observe what a **missing `no_log`** leaks at higher verbosity, and fix it.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/verbosite-vvv/

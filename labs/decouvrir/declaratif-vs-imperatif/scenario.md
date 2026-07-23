# Context — The script that adds a line every night

A colleague deploys the landing page of **web1.lab** with a Bash script fired
by cron. It works. Except visitors now read *"Servi par web1.lab"* three times
on the home page, then four, then five. Nobody touched the page: the script
appends the line at every run and never asks whether it is already there. The
incident is small, the lesson is not.

From **control-node.lab**, you are going to watch why the same job, written
declaratively, cannot drift.

Your mission:

1. Run the **Bash script three times** against `web1.lab` and watch the line
   counter climb: that is drift, live.
2. Reset the node, then run the **playbook three times** and observe the page
   stay at exactly one line.
3. Read the second `PLAY RECAP`: **`changed=0`** is the mechanical proof of
   idempotence, not a matter of opinion.
4. Compare the two files and name what the `lineinfile:` module compares before it
   writes anything at all.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/declaratif-vs-imperatif/

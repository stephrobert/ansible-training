# Context — The SSH session dies before the job does

The nightly maintenance job on **db1.lab** takes twenty minutes. The playbook
that launches it fails around minute ten, every time, on a broken SSH pipe.
Worse: nobody can say whether the job died with the connection or is still
grinding away on the host. Holding an SSH session open for the whole duration
of a long task is not a plan. Ansible has a proper answer: launch it, let go,
and come back for the result.

You rehearse the pattern from **control-node.lab** on a deliberately short job.

Your mission:

1. Fire a long task on `db1.lab` **in the background** and get control back
   immediately, without waiting for it to end.
2. Keep its **job id**: a fire-and-forget task nobody ever checks is a task
   whose failure you will never see.
3. Poll that job with **`async_status`** until it reports finished, with enough
   retries and delay to actually cover the run time.
4. Prove it landed: the marker file exists on `db1.lab` with the expected
   content, and the recap is coherent.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/async-poll/

# Context — The playbook that only your laptop can run

The release failed at 2am and the on-call engineer could not take over. The
playbook runs on your machine and only yours: you have a collection installed
that nobody else does, a Python library pinned by accident three months ago, and
an `ansible-core` version that no longer matches the one on the CI runner. Every
handover ends the same way, with a wiki page listing what to install and a
colleague halfway through it. The runtime has to travel with the playbook.

Your mission, from the project directory:

1. Pull an official **Execution Environment** image with Podman, so the entire
   Ansible runtime becomes one versioned artefact instead of a wiki page.
2. Declare it as the **default environment** for the project, and script the
   prerequisites check so a newcomer gets a working setup without asking anyone.
3. Run a playbook **inside** the EE against **web1.lab** and **db1.lab**, proving
   the container reaches the managed nodes as well as a local run would.
4. Compare the two runs, plain and containerised, and name what actually changed:
   what is now guaranteed, and what it costs you.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/presentation/

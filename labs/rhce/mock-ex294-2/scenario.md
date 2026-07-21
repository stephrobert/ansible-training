# Context — Four hours, no search engine, and a machine you have never seen

This is the second mock. Same exam, different room: an Apache and valkey stack
where the first mock ran nginx and mariadb, other users, another disk layout,
other ports and another schedule. Everything a candidate could have memorized
from the first attempt is worthless here, and that is the point. What survives
the change of scenery is the skill.

Nineteen independent tasks across the four lab machines, four hours, and the
only documentation you get is what ships with Ansible. A task counts when it
executes clean and its result holds up under inspection, and not one second
before.

Your mission, from **control-node.lab**:

1. Start the clock and work the nineteen tasks: inventories and variables, files,
   packages, services, users, storage, security, roles and vault, then error
   handling, rolling waves, delegation, tags, scheduled jobs, custom facts and a
   content collection installed from a `requirements.yml`, across **web1.lab**,
   **web2.lab** and **db1.lab**.
2. **Verify each task as you finish it.** Candidates who leave verification for
   the end discover their mistakes with forty minutes left and no time to fix them.
3. Manage the clock like an exam, not a lab: a task that resists gets abandoned
   and revisited.
4. Debrief honestly at the end. What you had to look up is your real weakness, and
   it is the only useful output of a mock exam. Under three hours means ready.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/certifications/rhce/

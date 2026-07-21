# Context — Everyone on the team googles the same command every week

`ansible-galaxy` does seven different jobs and nobody on the team remembers more
than three of them. Someone reinvents a role skeleton by hand because they forgot
`init` exists. Someone installs a collection into the wrong path. Someone tries
to publish and discovers, at the worst moment, that a tarball has to be built
first. Two new joiners start Monday, and the onboarding answer cannot keep being
"ask in the chat".

Your mission, from the project directory:

1. Produce the team's reference for the CLI, covering **scaffolding** a role and
   a collection, **installing** from Galaxy and from Git, and **listing** what is
   actually present locally.
2. Cover the publication path end to end: **build** the tarball, **publish** it
   with an API token, and **verify** the integrity of what came back down.
3. For each command, state where it writes, since that is the trap: roles and
   collections do not land in the same place.
4. Check your reference against the real binary rather than against memory.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ansible-galaxy-cli/

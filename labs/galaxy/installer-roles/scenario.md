# Context — The same project, two machines, two results

The deployment worked in July and fails today, on the same commit. Nothing in the
repository changed: an upstream role published a new major version overnight, and
the project installs it unpinned, so every machine pulls whatever is newest at
the moment it runs. Your laptop, the CI runner and the colleague who onboarded
last week are each running a different codebase from identical Git checkouts.

Your mission, from the project directory:

1. Declare **every** dependency of the project in one manifest: roles from
   Galaxy, roles pulled straight from **Git**, and collections, so nothing is
   installed by folklore any more.
2. **Pin** all of them, and pick the pinning that fits each case: an exact
   version where a surprise is unacceptable, a bounded range where it is not.
3. Distinguish the two install paths, since roles and collections do not land in
   the same place, and neither is versioned by the repository.
4. **Vendor** the one role you cannot afford to lose into the project itself, and
   justify why that one and not the others.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/installer-roles-galaxy/

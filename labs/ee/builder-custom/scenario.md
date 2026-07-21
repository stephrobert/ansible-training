# Context — No public image fits, and the audit wants to know what runs

None of the official EEs work for you. The minimal one lacks the collections your
playbooks call; the fat ones carry hundreds of megabytes you will never use and
an `ansible-core` you do not control. Meanwhile the security team asks a fair
question: what exactly is running on the automation hosts? "Whatever `:latest`
resolved to on build day" is not an answer they will accept, and it is not one
you can reproduce either.

Your mission, from the project directory:

1. Write the recipe for a **custom EE**, on the current schema, based on a minimal
   image and built with Podman.
2. **Pin everything**: `ansible-core`, every collection, every Python dependency
   to an exact version, and declare the system dependencies the image needs.
3. Inspect the container file the build generates, so you know what is being
   assembled instead of trusting a black box.
4. Test the resulting image, then push it to a **private registry** so the team
   consumes a version, not a moving tag.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/ee-builder/

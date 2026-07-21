# Context — You need the vault password just to read a port number

Onboarding hit a wall this week. A new colleague wanted to know which port the
web servers listen on. That value is public, uncontroversial, and locked inside
an encrypted `group_vars` file next to an admin token, so answering the question
required handing over the vault password. The team's config and the team's
secrets are living in the same file, and the secret is setting the access rules
for both.

Your mission, from **control-node.lab**:

1. Split each `group_vars/<group>/` in two: the public configuration in clear
   text, the secrets in a **separate encrypted file** loaded from the same place.
2. Adopt a naming convention that makes a sensitive variable recognisable at a
   glance, without opening anything.
3. Confirm Ansible merges both files transparently at run time: prove on
   **web1.lab** that public values and decrypted secrets, coming from the `all`
   group and from the web group, all land in the same play.
4. Check the payoff: `main.yml` is readable, and diffs on it stay reviewable.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/playbooks-mixtes/

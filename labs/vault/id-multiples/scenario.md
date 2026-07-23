# Context — One vault password means the interns can read production

Every secret in the repository is encrypted with the same vault password, and
that password is handed to anyone who needs to deploy to dev. Which means the
intern who deployed to dev this morning can decrypt the production database
credentials, and nothing in the tooling would stop them or even record it. The
secrets are encrypted. They are not compartmented, and that is a different thing.

Your mission, from **control-node.lab**:

1. Give each environment its **own labelled vault identity** and its own password,
   so holding the dev key decrypts dev and nothing else.
2. Lay the secrets out per environment under `group_vars/`, dev on **web1.lab**
   and prod on **db1.lab**, each group carrying only what belongs to it.
3. Run a single play across **both** environments and have Ansible decrypt each
   file with the right identity, proving the two are never confused.
4. Read the encrypted header and say which identity a file belongs to without
   decrypting it, then state who on the team gets which password.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/vault-id-multiples/

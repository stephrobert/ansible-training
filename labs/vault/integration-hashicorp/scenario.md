# Context — An admin left, and nobody can say what she could read

The offboarding checklist asked a simple question and the team could not answer
it: which secrets did she have access to, and which ones are now compromised? Every
secret in the repository is encrypted with a vault password she had, so the answer
is "all of them", and the fix is to rotate everything by hand. There is no audit
trail, no rotation, no expiry. Ansible Vault protects a file. It does not manage a
secret's life.

Your mission, from the project directory:

1. Stand up a **local secret server** (HashiCorp Vault or its open-source fork)
   and store the application's credentials in it, so the secret lives in a system
   that can log, rotate and expire it.
2. Have a playbook **read** the secret at run time through the dedicated
   collection, with the mount point stated explicitly and **no secret value
   written in the YAML**, ever.
3. Keep the setup swappable between the two implementations: the API is the same,
   and the licence question should not rewrite your playbooks.
4. Compare the ways to authenticate (token, AppRole, JWT) and say which belongs
   to a human, which to CI, and why the dev token belongs to neither.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/integration-hashicorp-vault/

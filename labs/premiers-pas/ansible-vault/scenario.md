# Context — Three secrets that must never reach a log

The application on **db1.lab** needs a config file carrying a database
password, a JWT secret and a Redis token. Last time this was done by hand, the
three values ended up in clear text in the Git history *and* in the CI console
output. The audit left you one rule: secrets live encrypted in the repo, they
are decrypted only at run time, and they appear in **no** Ansible output.

From **control-node.lab**, you build that chain end to end.

Your mission:

1. Keep the vault password in a `0600` file, gitignored, and nowhere else.
2. Encrypt the three secrets in a **Vault YAML file**, then verify on disk that
   it really begins with the `$ANSIBLE_VAULT` header.
3. Consume it through **`vars_files`** to render `/tmp/db1-app.conf` on
   `db1.lab`, owner `root`, mode `0600`.
4. Silence the task that handles them so the values never surface in the
   console — and remember that this keyword belongs to the task, not to the
   module.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/premiers-pas/premiers-pas-ansible-vault/

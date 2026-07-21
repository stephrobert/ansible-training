# Context — The shared spreadsheet of passwords has to die

Your playbooks get their infrastructure secrets from a proper secret server. The
humans do not. The SaaS accounts, the third-party API keys, the certificate
passphrases and the admin login everyone uses live in a spreadsheet on a shared
drive, because the team needs to read them with their eyes, not just from a
playbook. Those secrets need a home that serves both: a web UI a human will
actually use, and an interface Ansible can query.

Your mission, from the project directory:

1. Stand up a **local Passbolt** instance with its database, and set up the admin
   account and the **OpenPGP key** that identifies you to it.
2. Have a playbook fetch a secret from it through the dedicated collection,
   authenticating with your private key and passphrase, with **no secret value
   hardcoded** in the YAML.
3. Silence the sensitive tasks so the secret never surfaces in the output or the
   logs, whatever the verbosity.
4. Position the tool against a HashiCorp-style server: its identity model is a
   key per human, not a token per machine. Say which secrets go where.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/integration-passbolt/

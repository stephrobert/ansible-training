# Context — Eight commands, and one that keeps you out of the news

First week on the team. In a single afternoon you are asked what an inventory
really resolves to, which arguments a module actually takes, why last night's
run was slow, and where the production database password lives. You could open
eight browser tabs. Or you could learn that each answer is a **command shipped
with Ansible** — and that the last one, `ansible-vault`, is all that stands
between your Git repo and a leaked credential.

Everything runs from **your control node**.

Your mission:

1. Tour the toolbox: ad-hoc `ansible`, `ansible-doc`, `ansible-config`,
   `ansible-inventory`, `ansible-galaxy` and `ansible-lint`, each answering one
   real question.
2. Then prove you can handle a secret: script the creation of a small
   `vault-secret.yml` holding an API key and a database password.
3. **Encrypt** it with a password file kept in `0600`, and verify on disk that
   the file really starts with the `AES256` Vault header.
4. **Read it back** without decrypting it in place, and fail loudly (exit 1) if
   anything is off.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/prise-en-main-cli/

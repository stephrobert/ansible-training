# Context — The role ships its own secrets, and nobody can change them

The `secured_app` role travels with the credentials it needs, encrypted inside
the role. That solves distribution and creates a new problem: a team that wants
its own database password has to decrypt the role's internals, edit them, and
re-encrypt. So they fork the role. Three forks later, a security fix has to be
applied four times. The role's secrets are its business; the values a caller uses
are not.

Your mission, from **control-node.lab**:

1. Keep the role's secrets **encrypted inside the role**, in the variables file
   the caller is not supposed to touch.
2. Expose them through **public, overridable variables** that point at the
   encrypted ones, so the caller sees a knob and never the ciphertext.
3. Prove the indirection works both ways on **db1.lab**: an untouched default
   resolves to the decrypted secret, and a value overridden from the play wins.
4. Explain the precedence you just relied on, and why the public variable had to
   live where it does for the override to be possible at all.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/vault-dans-roles/

# Context — Nobody can review a wall of ciphertext

Encrypting whole files worked, and now the reviews are blind. Your
`host_vars/db1.lab.yml` holds a listening port, a version, a username and exactly
one password, and because of that one password the entire file is ciphertext. A
diff on it says a blob changed. Reviewers approve without knowing whether someone
bumped a port or swapped a credential. Encrypting the file protected the secret
and destroyed the review at the same time.

Your mission, from **control-node.lab**:

1. In `host_vars/db1.lab.yml`, keep the non-sensitive values **readable** and
   encrypt only the password, as a single inline value inside an otherwise plain
   YAML file.
2. Have Ansible pick that value up transparently at run time, with no extra step
   from the caller.
3. Prove on **db1.lab** that both kinds of variable arrive usable side by side:
   the clear username exactly as written, and the decrypted password.
4. Settle the rule for the team: when an inline value is the right call, and when
   the whole file should be encrypted instead.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/chiffrer-fichier-variable/

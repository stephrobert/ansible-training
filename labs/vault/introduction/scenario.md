# Context — The database password is in the Git history

The security review found it this morning: a `db_secrets.yml` committed in clear
text eighteen months ago, still readable by anyone who can clone the repository.
Deleting the file changes nothing, Git remembers. The password is rotating today,
and the new one is not going anywhere near a plain YAML file. What the repository
holds from now on is ciphertext, decrypted only at run time on the control node.

Your mission, from **control-node.lab**:

1. Encrypt the two secrets files the application needs, so what lands in Git is
   unreadable without the vault password, and confirm the encryption is real by
   inspecting the file.
2. Read and modify an encrypted file **without** leaving a decrypted copy behind
   on disk.
3. Have a playbook consume **both** encrypted files in a single run and prove, on
   **db1.lab**, that their values arrived intact, in a file readable only by root.
4. Handle the rotation itself: change the vault password on an existing file, and
   know how to bring a file back to clear text when it stops holding a secret.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/ansible-vault-introduction/

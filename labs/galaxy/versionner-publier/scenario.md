# Context — You renamed a variable and broke four teams

Your `webserver` role is used across the company. Last release you renamed an
input variable, shipped it as a bugfix, and four projects broke on their next
run. They had done nothing wrong: they pinned a patch range, because a patch is
supposed to be safe. The break was real, but the lie was in the version number.
Consumers cannot pin sanely if the publisher's numbering means nothing.

Your mission, from the project directory:

1. Set the rule for **which digit moves** and when: what forces a major bump,
   what earns a minor, what is genuinely a patch, and where a rename lands.
2. Keep a **changelog** consumers can act on, sorted by version and by nature of
   change, so a reader can tell in ten seconds whether an upgrade will hurt.
3. Cut the release as an **annotated Git tag**, and document the procedure so it
   is reproducible by someone who is not you.
4. Automate the publish from CI on the tag, and document how the **consumer**
   should pin the result.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/versionner-publier/

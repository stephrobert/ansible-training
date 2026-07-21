# Context — A typo that only blew up ten minutes in

Yesterday a colleague called your `webserver` role with `webserver_state:
enabled`. There is no such choice. Ansible said nothing, ran happily for ten
minutes, then died deep inside a package task with a stack trace nobody could
read. The value was wrong from the first second, but the role had no way to say
so. A role that trusts its inputs makes its users pay for its silence.

Your mission, from **control-node.lab**:

1. Deploy the `webserver` role on **db1.lab** with **valid** inputs: listening
   port **8090**, plus a package state and a service state chosen from the
   allowed values, and a custom index page.
2. Have the role **type, constrain and document** its input variables so a wrong
   value is rejected **before the first task runs**, not ten minutes later.
3. Feed it a deliberately invalid value and read the rejection message: it must
   name the variable and list what was allowed.
4. Check that a run with valid values still passes the validation step cleanly.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/argument-specs/

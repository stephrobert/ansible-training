# Context — Hand out SSH access without handing out the whole server

Password authentication is being retired on **db1.lab**, and three accesses
must land before it goes: Alice works from anywhere and needs an ordinary key;
Bob only ever connects from the office subnet, and security wants his key
useless from anywhere else; the backup robot needs an account of its own, but a
robot key that opens an interactive shell is a spare set of admin credentials
sitting in a CI runner. Everything is provisioned from **control-node.lab**.

Your mission:

1. Create the two user accounts on **db1.lab**, then install **Alice's personal
   key** with no restrictions.
2. Install **Bob's key restricted to the office subnet**, with no terminal
   allocation.
3. Give the backup robot a key that can **only trigger the backup script**, with
   no shell, no tunnels and no X11 forwarding: an intercepted key must be worth
   nothing.
4. Add the keys **without wiping** those already in place: locking the trainer
   out of the box is not part of the exercise.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-authorized-key/

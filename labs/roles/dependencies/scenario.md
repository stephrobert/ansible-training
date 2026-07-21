# Context — Everyone forgets the prerequisites

Every playbook that uses the `webserver` role starts with the same two chores:
put SELinux in the right mode with the right booleans, then open the ports in
firewalld. Whoever forgets one gets a web server that starts and serves nothing,
and spends an afternoon on it. Those prerequisites are not the caller's problem:
the role knows what it needs, so the role should say it, once, and be obeyed.

Your mission, from the project directory, against **db1.lab**:

1. Have the `webserver` role **declare** the two roles it depends on,
   `selinux_setup` then `firewall_setup`, so a caller can never skip them again.
2. Pass each dependency the variables it needs: SELinux in `enforcing`, and
   **443/tcp** opened by the firewall role, without leaking them into the
   parent role.
3. Write a play that consumes **only** the `webserver` role, listening on
   8081, and prove the real execution order on the target: each role logs its
   passage in `/tmp/deps-order.txt`, and that file must read dependencies
   first, parent role last.
4. Walk into the diamond: when two dependencies share a third one, decide how
   many times that shared role runs, and what changes the answer.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/dependencies/

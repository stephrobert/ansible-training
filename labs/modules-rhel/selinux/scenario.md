# Context — Serve the app from a custom directory, with SELinux still on

The application deployed on **db1.lab** lives outside the default web root, and
nginx returns 403 on every file even though the permissions are right. It also
needs to reach a backend API, and those outbound calls are refused too. A
colleague found the fastest fix and applied it: SELinux disabled. That is not a
fix, that is a finding on the next audit, and the RHCE exam scores it as a
failure. You put the protection back and make the app work **with** it, from
**control-node.lab**.

Your mission:

1. Install the SELinux prerequisites on **db1.lab**, without which the modules
   fail with an unhelpful error, then put SELinux back to **enforcing** under
   the targeted policy.
2. Allow the web server's **outbound network connections** through the right
   boolean, **persistently**: a boolean that resets at reboot fixes nothing.
3. Declare the correct **file context on the custom application directory**, as
   a path pattern covering the tree and not just the directory itself.
4. **Apply that context to the files already there**: declaring it in the policy
   leaves existing files untouched, and nginx keeps returning 403.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-selinux/

# Context — Replace the blind sleeps holding the deployment together

The deployment playbook for **db1.lab** is riddled with `sleep 30`, each one
added the day something went wrong. Nobody dares remove them, and they still are
not enough: the job sometimes finishes in two seconds, sometimes in forty, and
the play carries on regardless of what actually happened. Waiting blindly is not
synchronizing. You rewrite the sequence from **control-node.lab** so it waits for
**events**, not for the clock.

Your mission:

1. On **db1.lab**, launch the background job that lays down its marker after a
   few seconds, then **wait for the marker to appear** with a timeout that
   fails fast instead of hanging for minutes.
2. Add a short **stabilization pause**, the one case where a timer is honest,
   and know that it blocks the control node, not the managed node.
3. **Check the service is actually listening** on its port before declaring
   success: a service that is `started` is not always a service that answers,
   and the module only tests TCP.
4. Write the success marker once, and only once, the synchronization holds.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-wait-for-pause/

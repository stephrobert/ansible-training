# Context — Half the fleet updated is worse than none

Tuesday's config push reached **web1.lab**, failed on **web2.lab**, and
stopped there. That is the default behaviour, and it sounds reasonable until
you look at the result: two webservers behind the same load balancer, running
two different configurations, giving two different answers to the same request.
Support spent a day chasing a bug that only appeared every other refresh. For
this kind of change, half-applied is worse than not applied at all.

You set the policy at the **play level**, from **control-node.lab**.

Your mission:

1. Write a two-step deployment on both webservers: stage the release, run a
   health check, then activate the release. Each step leaves a per-host
   marker file so nothing can be claimed without evidence.
2. Make the health check fail on the host named by a `fail_host` variable
   (`none` by default), so an incident can be simulated on demand with
   `-e fail_host=web1.lab`.
3. Enable the play keyword that **stops the entire play** the moment any host
   fails: when web1 fails its health check, web2 must NOT activate its
   release, even though web2 itself never failed. That absence is what the
   validation checks.
4. Then place it precisely: compare it with the default behaviour, and with
   `max_fail_percentage`, which tolerates a threshold rather than demanding
   perfection. And work out what it does once combined with `serial`.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/any-errors-fatal/

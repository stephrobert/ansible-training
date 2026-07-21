# Context — Fix the clock drift and prove the host booted clean

Correlating logs across the fleet turned into guesswork last week: **web1.lab**
drifts several seconds off, so its timestamps no longer line up with the other
servers during an incident. Time synchronization must be running and, above all,
come back **on its own after a reboot**, which the manual `systemctl start`
never guaranteed. The ops team also wants a boot marker: a small unit that drops
a flag at startup, so a host that came up clean can be told at a glance.

Your mission:

1. From **control-node.lab**, install the time synchronization service on
   **web1.lab**, then make it **running now and enabled at boot**: the two are
   not the same thing.
2. Drop a **custom unit file** `lab-marker.service` that lays down its flag
   once at startup and stays marked active afterwards.
3. Make systemd **actually take the new unit into account** before enabling and
   starting it, otherwise it stays invisible behind the cache.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-systemd/

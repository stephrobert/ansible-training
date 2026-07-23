# Context: the file nobody should have written

The audit came back. On db1.lab the clock drifts, the NTP servers are whatever
DHCP felt like pushing, and the `/etc/chrony.conf` in place carries three
generations of contradictory comments. The colleague who "fixed it by hand last
time" has left. Nobody dares touch it, because nobody knows what breaks if they
do.

Red Hat already wrote the thing you were about to rewrite. The `timesync` system
role takes an intent expressed as variables and returns a generated, signed,
consistent file, across every RHEL version. It is an EX294 objective in its own
right, and it is also the only way to leave that file repairable by the next
person.

Your mission, from the project directory, against **db1.lab**:

1. Consume the **`timesync`** system role at play level, by fully qualified
   name. You must not write a single line of `chrony.conf` yourself.
2. Declare **three NTP servers**: `0.fr.pool.ntp.org` as the preferred source,
   `1.fr.pool.ntp.org`, and `2.fr.pool.ntp.org` capped at a maximum polling
   interval. All three with `iburst`.
3. Bring the **clock stepping threshold** down to 0.1 second, and require **two
   sources** to agree before any adjustment.
4. Remove what the distribution had put there: the default `pool` and the DHCP
   back door.
5. Prove it on the machine, not in your editor: `chronyd` must run with those
   three sources, and the clock must be locked onto one of them.

The play must be **idempotent**: replayed, it rewrites nothing and restarts
nothing.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/

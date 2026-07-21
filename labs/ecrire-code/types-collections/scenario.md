# Context — Staging keeps leaking into the production config

The service catalogue is a single list: name, port, tier. Four entries today,
forty next quarter. The file feeding production monitoring is maintained by
hand from that list, and the last update quietly slipped a staging port into
it. Nobody noticed until monitoring woke someone at 3 a.m. over a dev database.
The catalogue is fine. Copying it by hand is what keeps failing.

From **control-node.lab**, you generate the production view from the catalogue
itself.

Your mission:

1. Declare the catalogue on `db1.lab` as a **list of dicts**, each entry
   carrying its name, port and tier.
2. Generate `/tmp/services-production.txt` holding **only** the `production`
   tier, one `<name>:<port>` per line.
3. Do the filtering **in the data**, not by hand: the staging and dev entries
   must never reach the file, whatever order the catalogue is written in.
4. Check the result is exactly the two expected lines and nothing else, then
   reach a nested field to build each line.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/types-collections/

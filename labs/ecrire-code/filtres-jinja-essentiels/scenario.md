# Context — The data comes in dirty, the config must come out clean

The values feeding your configs arrive from three sources and none of them
agrees with the others. One field comes padded with spaces and shouting in
capitals. Two package lists overlap and must become a single set. The service
catalogue mixes prod and staging. A base config needs a TLS override stacked on
top. And one variable is sometimes plainly absent — which does not warn you, it
kills the templating halfway through the run.

You clean all of it **in the data**, on `db1.lab`, from **control-node.lab**.

Your mission:

1. Normalise a dirty string, then merge two package lists into one
   deduplicated, sorted set.
2. Extract the **production** services from a list of dicts and keep only their
   names.
3. Merge a base config with its overrides, and understand what a flat merge
   does to the keys underneath.
4. Make a missing variable **fall back** to a value instead of taking the run
   down with it, then write the six results on db1.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/filtres-jinja-essentiels/

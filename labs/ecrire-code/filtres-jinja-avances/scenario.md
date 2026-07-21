# Context — Four transformations nobody should do by hand

The integration you are wiring needs four things Ansible will not hand you
ready-made: the machine's role prefix, buried inside its FQDN; a Basic auth
header, which means the credentials pair must be base64 encoded; a list that
arrives nested from another team's export; and a sha256 fingerprint so you can
tell whether a payload actually changed. All four are done by hand today, from
a wiki page of copy-pasteable commands, and the wiki page is wrong.

You do them in the data, on `db1.lab`, from **control-node.lab**.

Your mission:

1. **Extract** the role prefix from an FQDN with a regex, anchored so it stops
   before the first digit.
2. **Encode** the credentials pair to base64, and stay clear about what that
   is: encoding, never encryption.
3. **Flatten** the nested list into a flat one, and check how deep the filter
   goes before it gives up.
4. Produce a **sha256** fingerprint of a string, then write the four results on
   db1.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/filtres-jinja/

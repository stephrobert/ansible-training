# Context — The inventory spreadsheet nobody trusts

The capacity report is a spreadsheet, filled in by hand, and it has been wrong
for months: db1's memory figure predates its last resize, and web1's IP was
updated when the network changed, in one of the two tabs. Meanwhile the
machines know all this about themselves, and Ansible collects it at the start
of every run before throwing it away. From **control-node.lab**, you build a
summary that reads the machines instead of the spreadsheet.

Your mission:

1. On `db1.lab`, write `/tmp/facts-summary.txt` carrying its own inventory
   name, its distribution and its total memory, **read from the facts** rather
   than typed in.
2. Add how many hosts the `webservers` group really contains, taken from the
   inventory itself and not from memory.
3. Add **web1.lab's IP address** through `hostvars`, from a play running on
   db1.
4. Make sure web1's facts actually exist before you read them: `hostvars` only
   carries what has already been gathered. Then cut the collection cost with
   `gather_subset`.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/facts-magic-vars/

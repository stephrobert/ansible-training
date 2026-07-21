# Context — Your team's automation does not fit in a role any more

The team's shared automation has outgrown what a role can carry. There is a role
for nginx, a Python module someone wrote to health-check the app, and three
playbooks that tie them together, each living in its own repository with its own
version, and no version of the set as a whole. Users install three things and hope
the combination works. Besides, the platform the company publishes to no longer
accepts standalone roles at all.

Your mission, from **control-node.lab**:

1. Scaffold a **collection** under your namespace and fill in its manifest:
   namespace, name, version, dependencies and tags. This is now the versioned unit.
2. Bring in a **role**, and add a **Python module** of your own with the
   documentation, examples and return block a module is expected to carry.
3. Account for the standard layout: what belongs in plugins, roles, playbooks,
   meta and tests, and why a module cannot just be dropped anywhere.
4. **Build the tarball** and check the collection passes sanity, because a
   collection that fails sanity is not distributable.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/creer-collection-custom/

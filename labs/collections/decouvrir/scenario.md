# Context — "Module not found", and the module is right there

A playbook that has worked for two years fails on the new control node: module
not found. The module exists, it is just called by its short name, and the
collection that provides it is not installed here. Nobody can say which
collections this environment actually carries, or where they came from. Meanwhile
the linter has started rejecting short names outright, so "it used to work" is
about to stop being an argument across the whole codebase.

Your mission, from **control-node.lab**:

1. Take inventory of the collections actually installed in the environment, with
   their **versions** and where they live on disk, and have the play write that
   inventory to a file on **db1.lab** rather than to your scrollback.
2. Read a collection's own metadata to find who publishes it, which version it
   claims, and what it depends on.
3. Walk its layout and say what a collection can ship beyond modules: plugins,
   roles, playbooks, docs.
4. Take a module you call every day, find the collection it comes from, and write
   its **fully qualified name**. That is what the linter will demand tomorrow.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/

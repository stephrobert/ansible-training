# Context — The playbook you inherited was written in 2016

You take over a repo nobody has touched in years. It works. It also fails the
CI lint gate on its very first file: `with_items` everywhere, a `with_dict` on
the ports mapping, a `with_subelements` nobody dares read out loud. The syntax
is deprecated, not broken, which is exactly why it is still there. It will keep
working right until the release that removes it, and that release is not far
off.

You modernise the iterations on `db1.lab`, from **control-node.lab**.

Your mission:

1. Rewrite the simple list iteration with **`loop:`**, the modern one-to-one
   replacement.
2. Migrate the port mapping: a dict does **not** iterate directly. Convert it
   to a list of pairs and reach both the key and the value.
3. Keep the console readable while you are in there: label each iteration by
   what it actually does.
4. Reach zero deprecation on `ansible-lint`, and find out which of these
   rewrites the linter can perform for you.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/boucles-with-deprecated/

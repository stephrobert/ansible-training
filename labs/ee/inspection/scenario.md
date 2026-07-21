# Context — Somebody picked an EE because it was first in the search results

The project standardised on an Execution Environment last quarter, chosen the way
these things usually are: someone found an image name in a blog post and it
worked. It weighs two gigabytes, ships collections nobody uses, and still lacks
the one your playbooks need, which a colleague now installs at run time inside the
container, quietly defeating the whole point. Before you build your own, you need
to be able to say what is actually inside these things.

Your mission, from the project directory:

1. Script the inspection of an EE: **list the collections it embeds**, the
   `ansible-core` version it carries, its system packages and its real size.
2. Run that inspection across **three** official EEs, one aimed at authoring, one
   at a controller, one deliberately minimal, and compare the results.
3. Read a module's documentation **as the EE sees it**, since what is documented
   inside the image is what your playbook can actually call.
4. Turn the comparison into a **choice per use case**: which EE for training,
   which for a controller, which for lean production, and why.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/lookup-doc/
